# app.py
# PyInstaller build command:
# Windows: pyinstaller --noconfirm --onedir --windowed --copy-metadata flask --copy-metadata werkzeug --add-data "static;static" --add-data "templates;templates" --add-binary "bin/yt-dlp.exe;bin" --add-binary "bin/ffmpeg.exe;bin" app.py
# macOS: pyinstaller --noconfirm --onedir --windowed --copy-metadata flask --copy-metadata werkzeug --add-data "static:static" --add-data "templates:templates" --add-binary "bin/yt-dlp:bin" --add-binary "bin/ffmpeg:bin" app.py

import os
import shutil
import sys
import threading
import time
import uuid
import webbrowser
import subprocess
import requests
from packaging import version
from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------
# 1. 전역 설정 및 초기화
# ---------------------------------------------------------

# --- 버전 및 업데이트 정보 ---
CURRENT_VERSION = "1.0.0"
GITHUB_REPO_OWNER = "anoBand"
GITHUB_REPO_NAME = "youtube_score_capturer"
UPDATE_INFO = {
    "needs_update": False,
    "latest_version": None,
    "download_url": None
}

# --- 모듈 임포트 ---
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

# --- 임시 폴더 설정 ---
if getattr(sys, 'frozen', False):
    EXE_LOCATION = os.path.dirname(sys.executable)
else:
    EXE_LOCATION = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(EXE_LOCATION, 'temp')
if not os.path.exists(TEMP_BASE_DIR):
    os.makedirs(TEMP_BASE_DIR)


# ---------------------------------------------------------
# 2. 자동 실행 및 백그라운드 작업
# ---------------------------------------------------------

def launch_browser():
    """서버 시작 후 브라우저를 자동으로 엽니다."""
    try:
        webbrowser.open_new("http://127.0.0.1:5000")
    except Exception as e:
        print(f"Browser launch failed: {e}")


def update_yt_dlp_binary():
    """yt-dlp 바이너리를 자동으로 업데이트합니다."""
    ytdlp_path = get_bin_path('yt-dlp')
    startup_info = get_startup_info()
    try:
        subprocess.run(
            [ytdlp_path, "-U"],
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            check=True
        )
    except Exception:
        pass


def check_for_updates():
    """GitHub에서 최신 릴리스를 확인하고 업데이트 정보를 설정합니다."""
    global UPDATE_INFO
    api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        latest_release = response.json()
        latest_version_str = latest_release.get("tag_name", "").lstrip('v')
        
        if latest_version_str:
            current = version.parse(CURRENT_VERSION)
            latest = version.parse(latest_version_str)
            if latest > current:
                UPDATE_INFO["needs_update"] = True
                UPDATE_INFO["latest_version"] = latest_version_str
                UPDATE_INFO["download_url"] = latest_release.get("html_url")
    except (requests.RequestException, version.InvalidVersion):
        pass  # 네트워크 오류 또는 버전 파싱 실패 시 조용히 실패


def cleanup_worker():
    """만료된 임시 세션 폴더를 주기적으로 삭제합니다."""
    # Local environment: limit removed
    # 로컬 실행 환경에서는 세션 타임아웃이 불필요하므로 관련 로직을 비활성화합니다.
    # 주기적인 폴더 검사는 유지하되, 시간 기반 삭제 로직은 제거됩니다.
    while True:
        try:
            if os.path.exists(TEMP_BASE_DIR):
                # 기존 로직:
                # now = time.time()
                # for folder_name in os.listdir(TEMP_BASE_DIR):
                #     folder_path = os.path.join(TEMP_BASE_DIR, folder_name)
                #     if os.path.isdir(folder_path):
                #         if (now - os.path.getmtime(folder_path)) > 180:
                #             shutil.rmtree(folder_path)
                pass  # 아무 작업도 하지 않음
        except Exception:
            pass
        time.sleep(3600)  # 검사 주기를 1시간으로 늘림


def cleanup_temp_dir_startup():
    """시작 시 임시 폴더를 초기화합니다."""
    if os.path.exists(TEMP_BASE_DIR):
        for item in os.listdir(TEMP_BASE_DIR):
            item_path = os.path.join(TEMP_BASE_DIR, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.unlink(item_path)
            except Exception:
                pass


def time_to_seconds(time_str):
    """'HH:MM:SS' 또는 'MM:SS' 형식의 시간 문자열을 초로 변환합니다."""
    if not time_str: return None
    try:
        parts = list(map(int, str(time_str).split(':')))
        if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2: return parts[0] * 60 + parts[1]
        return int(parts[0])
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------
# 3. Flask 라우트
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html', version=CURRENT_VERSION)


@app.route('/check_update')
def check_update_route():
    """업데이트 상태를 JSON으로 반환합니다."""
    return jsonify(UPDATE_INFO)


@app.route('/inspect/<session_id>')
def inspect_page(session_id):
    session_dir = os.path.join(TEMP_BASE_DIR, session_id, 'images')
    if not os.path.exists(session_dir):
        return "Session expired or not found.", 404
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
        if not stream_url: return jsonify({'error': 'URL not found.'}), 400
        image_bytes = get_single_frame_as_bytes(stream_url, seconds)
        if image_bytes: return send_file(image_bytes, mimetype='image/jpeg')
        return jsonify({'error': 'Frame capture failed.'}), 500
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
            raise ValueError("No images extracted.")

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
# 4. 메인 실행
# ---------------------------------------------------------

if __name__ == '__main__':
    cleanup_temp_dir_startup()

    # 백그라운드 스레드 시작
    threading.Thread(target=cleanup_worker, daemon=True).start()
    threading.Thread(target=update_yt_dlp_binary, daemon=True).start()
    threading.Thread(target=check_for_updates, daemon=True).start()

    # 브라우저 자동 실행 예약
    threading.Timer(1.5, launch_browser).start()

    # Flask 서버 실행
    app.run(host='127.0.0.1', port=5000, debug=False)