# app.py
# PyInstaller build command (example):
# Windows: pyinstaller --noconfirm --onedir --windowed --add-data "static;static" --add-data "templates;templates" --add-binary "bin/yt-dlp.exe;bin" --add-binary "bin/ffmpeg.exe;bin" app.py
# macOS: pyinstaller --noconfirm --onedir --windowed --add-data "static:static" --add-data "templates:templates" --add-binary "bin/yt-dlp:bin" --add-binary "bin/ffmpeg:bin" app.py

import os
import shutil
import sys
import threading
import time
import uuid
import webbrowser
import subprocess
from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from flask_cors import CORS

# 모듈 임포트
from modules.youtube_downloader import get_video_stream_url, get_single_frame_as_bytes, download_youtube_video, \
    get_bin_path, get_startup_info
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images


def resource_path(relative_path):
    """ PyInstaller 임시 폴더(_MEIPASS) 또는 로컬 폴더에서 리소스 경로 반환 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


app = Flask(__name__,
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))
CORS(app)

# 실행 파일 위치 기준 임시 저장 경로 설정
if getattr(sys, 'frozen', False):
    EXE_LOCATION = os.path.dirname(sys.executable)
else:
    EXE_LOCATION = os.path.dirname(os.path.abspath(__file__))

TEMP_BASE_DIR = os.path.join(EXE_LOCATION, 'temp')

if not os.path.exists(TEMP_BASE_DIR):
    os.makedirs(TEMP_BASE_DIR)


# ---------------------------------------------------------
# 1. 유틸리티 및 브라우저 실행 함수
# ---------------------------------------------------------

def open_browser():
    """서버 주소로 기본 브라우저를 엽니다."""
    < comment - tag
    id = "3" > webbrowser.open_new("http://127.0.0.1:5000") < / comment - tag
    id = "3" >


def update_yt_dlp_binary():
    """앱 시작 시 포함된 yt-dlp.exe를 최신 버전으로 업데이트 시도합니다."""
    ytdlp_path = get_bin_path('yt-dlp')
    startup_info = get_startup_info()

    print(f"🔄 Checking for yt-dlp updates at: {ytdlp_path}")
    try:
        subprocess.run(
            [ytdlp_path, "-U"],
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            check=True
        )
        print("✅ yt-dlp update check completed.")
    except Exception as e:
        print(f"⚠️ Failed to update yt-dlp: {e}")


# ---------------------------------------------------------
# 2. 백그라운드 관리 (가비지 컬렉터 등)
# ---------------------------------------------------------

def cleanup_worker():
    """3분 이상 방치된 세션 폴더 자동 삭제"""
    while True:
        try:
            now = time.time()
            if os.path.exists(TEMP_BASE_DIR):
                for folder_name in os.listdir(TEMP_BASE_DIR):
                    folder_path = os.path.join(TEMP_BASE_DIR, folder_name)
                    if os.path.isdir(folder_path):
                        if (now - os.path.getmtime(folder_path)) > 180:
                            shutil.rmtree(folder_path)
                            print(f"🧹 GC: Cleaned up expired session: {folder_name}")
        except Exception as e:
            print(f"GC Worker Error: {e}")
        time.sleep(60)


def cleanup_temp_dir_startup():
    """시작 시 기존 임시 파일 제거"""
    if os.path.exists(TEMP_BASE_DIR):
        for item in os.listdir(TEMP_BASE_DIR):
            item_path = os.path.join(TEMP_BASE_DIR, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.unlink(item_path)
            except:
                pass


def time_to_seconds(time_str):
    if not time_str: return None
    try:
        parts = list(map(int, str(time_str).split(':')))
        if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2: return parts[0] * 60 + parts[1]
        return int(parts[0])
    except:
        return None


# ---------------------------------------------------------
# 3. 라우트 설정
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/inspect/<session_id>')
def inspect_page(session_id):
    session_dir = os.path.join(TEMP_BASE_DIR, session_id, 'images')
    if not os.path.exists(session_dir):
        return "세션이 만료되었거나 존재하지 않습니다.", 404
    images = sorted([f for f in os.listdir(session_dir) if f.endswith('.png')])
    return render_template('inspect.html', session_id=session_id, images=images)


@app.route('/temp_images/<session_id>/<filename>')
def serve_temp_image(session_id, filename):
    return send_from_directory(os.path.join(TEMP_BASE_DIR, session_id, 'images'), filename)


@app.route('/get_frame', methods=['POST'])
def get_frame():
    url = request.form.get('url')
    time_str = request.form.get('start_time')
    seconds = time_to_seconds(time_str) or 0
    try:
        stream_url = get_video_stream_url(url)
        if not stream_url: return jsonify({'error': '영상 주소를 찾을 수 없습니다.'}), 400
        image_bytes = get_single_frame_as_bytes(stream_url, seconds)
        if image_bytes: return send_file(image_bytes, mimetype='image/jpeg')
        return jsonify({'error': '이미지를 생성할 수 없습니다.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/execute', methods=['POST'])
def execute():
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(TEMP_BASE_DIR, session_id)
    os.makedirs(temp_dir)
    inspection_mode = request.form.get('inspection_mode') == 'true'

    try:
        youtube_url = request.form.get('url')
        start_time = time_to_seconds(request.form.get('start_time'))
        end_time = time_to_seconds(request.form.get('end_time'))

        config = {
            'x_start': int(request.form.get('x_start') or 0),
            'x_end': int(request.form.get('x_end') or 100),
            'y_start': int(request.form.get('y_start') or 0),
            'y_end': int(request.form.get('y_end') or 100),
            'threshold': float(request.form.get('threshold') or 5.0),
            'frame_interval_sec': float(request.form.get('frame_interval_sec') or 1.0)
        }

        video_path = download_youtube_video(youtube_url, temp_dir)
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(video_path, image_output_dir, start_time, end_time, **config)

        if not processed_image_paths:
            raise ValueError("추출된 이미지가 없습니다.")

        if inspection_mode:
            return jsonify({'inspection_needed': True, 'session_id': session_id})
        else:
            pdf_io = create_pdf_from_images(processed_image_paths)
            return send_file(pdf_io, as_attachment=True, download_name='score.pdf', mimetype='application/pdf')

    except Exception as e:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500
    finally:
        if not inspection_mode and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@app.route('/finalize', methods=['POST'])
def finalize():
    try:
        data = request.json
        session_id = data.get('session_id')
        selected_files = data.get('selected_images')
        session_dir = os.path.join(TEMP_BASE_DIR, session_id)
        image_paths = [os.path.join(session_dir, 'images', f) for f in selected_files]
        pdf_io = create_pdf_from_images(image_paths)
        return send_file(pdf_io, as_attachment=True, download_name='final_score.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------
# 4. 서버 메인 실행부
# ---------------------------------------------------------

if __name__ == '__main__':
    # 시작 시 정리 및 업데이트
    cleanup_temp_dir_startup()
    update_yt_dlp_binary()

    # 백그라운드 스레드 시작
    threading.Thread(target=cleanup_worker, daemon=True).start()

    # 브라우저 자동 실행 예약
    # debug=False 상태에서는 WERKZEUG_RUN_MAIN 체크 없이 바로 실행해도 무방합니다.
    threading.Timer(1.5, open_browser).start()

    # Flask 서버 실행
    app.run(host='127.0.0.1', port=5000, debug=False)