# app.py

import os
import shutil
import traceback
import subprocess
import sys
import threading
import time
import uuid
from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from flask_cors import CORS

# 커스텀 모듈 임포트
from modules.youtube_downloader import download_1080p_video_only as download_youtube_video
from modules.youtube_downloader import get_video_stream_url
from modules.image_processor import process_video_frames, get_single_frame_as_bytes
from modules.pdf_generator import create_pdf_from_images

app = Flask(__name__)
CORS(app)

# 프로젝트 내 임시 저장 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(PROJECT_ROOT, 'temp')

# 서버 시작 시 임시 폴더가 없다면 생성
if not os.path.exists(TEMP_BASE_DIR):
    os.makedirs(TEMP_BASE_DIR)


# ---------------------------------------------------------
# 1. 자동 업데이트 및 유지보수 스케줄러
# ---------------------------------------------------------

def update_yt_dlp():
    """서버 시작 시 yt-dlp 라이브러리를 최신 상태로 업데이트합니다."""
    print("Checking for yt-dlp updates...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✅ yt-dlp is up-to-date.")
    except Exception as e:
        print(f"⚠️ Failed to update yt-dlp: {e}")


def start_periodic_update():
    """24시간마다 yt-dlp를 업데이트하고 서버를 재시작합니다."""

    def job():
        while True:
            time.sleep(86400)
            print("🔄 Performing daily yt-dlp update...")
            update_yt_dlp()
            print("🛑 Restarting server to apply updates...")
            os._exit(0)

    thread = threading.Thread(target=job, daemon=True)
    thread.start()


# ---------------------------------------------------------
# 2. 백그라운드 가비지 컬렉터 (GC) - 3분 지연 삭제
# ---------------------------------------------------------

def cleanup_worker():
    """3분(180초) 이상 방치된 임시 세션 폴더를 자동으로 삭제합니다."""
    while True:
        try:
            now = time.time()
            if os.path.exists(TEMP_BASE_DIR):
                for folder_name in os.listdir(TEMP_BASE_DIR):
                    folder_path = os.path.join(TEMP_BASE_DIR, folder_name)
                    if os.path.isdir(folder_path):
                        # 폴더의 마지막 수정 시간(mtime) 확인
                        # 생성 후 접근이 없으면 mtime 기준으로 180초 뒤 삭제
                        if (now - os.path.getmtime(folder_path)) > 180:
                            shutil.rmtree(folder_path)
                            print(f"🧹 GC: Cleaned up expired session: {folder_name}")
        except Exception as e:
            print(f"GC Worker Error: {e}")
        time.sleep(60)  # 1분마다 체크 수행


def cleanup_temp_dir_startup():
    """서버 시작 시 기존의 모든 임시 파일을 제거합니다."""
    print("Cleaning up old temporary files on startup...")
    if os.path.exists(TEMP_BASE_DIR):
        for item in os.listdir(TEMP_BASE_DIR):
            item_path = os.path.join(TEMP_BASE_DIR, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Failed to delete {item_path}: {e}")


# ---------------------------------------------------------
# 3. 유틸리티 함수
# ---------------------------------------------------------

def time_to_seconds(time_str):
    """HH:MM:SS 또는 MM:SS 형식을 초(seconds) 단위로 변환합니다."""
    if not time_str:
        return None
    try:
        parts = list(map(int, str(time_str).split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return int(parts[0])
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------
# 4. 라우트 설정
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/inspect/<session_id>')
def inspect_page(session_id):
    """새 탭에서 열릴 검수 전용 페이지"""
    session_dir = os.path.join(TEMP_BASE_DIR, session_id, 'images')
    if not os.path.exists(session_dir):
        return "세션이 만료되었거나 존재하지 않습니다. (3분 경과 시 자동 삭제됨)", 404

    # 해당 폴더의 이미지 목록을 정렬하여 템플릿에 전달
    images = sorted([f for f in os.listdir(session_dir) if f.endswith('.png')])
    return render_template('inspect.html', session_id=session_id, images=images)


@app.route('/temp_images/<session_id>/<filename>')
def serve_temp_image(session_id, filename):
    """검수 페이지에서 임시 이미지를 표시하기 위한 엔드포인트"""
    return send_from_directory(os.path.join(TEMP_BASE_DIR, session_id, 'images'), filename)


@app.route('/get_frame', methods=['POST'])
def get_frame():
    url = request.form.get('url')
    time_str = request.form.get('start_time')
    if not url:
        return jsonify({'error': 'URL이 필요합니다.'}), 400

    seconds = time_to_seconds(time_str) or 0
    try:
        stream_url = get_video_stream_url(url)
        if not stream_url:
            return jsonify({'error': '영상 주소를 찾을 수 없습니다.'}), 400

        image_bytes = get_single_frame_as_bytes(stream_url, seconds)
        if image_bytes:
            return send_file(image_bytes, mimetype='image/jpeg')
        return jsonify({'error': '이미지를 생성할 수 없습니다.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/execute', methods=['POST'])
def execute():
    # 고유 세션 ID 생성 (검수 페이지 연동을 위해 uuid 사용)
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(TEMP_BASE_DIR, session_id)
    os.makedirs(temp_dir)

    # 검수 모드 여부 확인 (문자열 'true'로 넘어옴)
    inspection_mode = request.form.get('inspection_mode') == 'true'
    print(f"Request: {session_id}, Inspection: {inspection_mode}")

    try:
        data = request.form
        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL이 필요합니다.'}), 400

        start_time = time_to_seconds(data.get('start_time'))
        end_time = time_to_seconds(data.get('end_time'))

        # 5분 제한 유효성 검사
        start_sec = start_time if start_time is not None else 0
        if end_time is not None and (end_time - start_sec) > 300:
            return jsonify({'error': '5분 이상의 영상은 구간을 나눠서 입력해 주세요.'}), 400

        config = {
            'x_start': int(data.get('x_start') or 0),
            'x_end': int(data.get('x_end') or 100),
            'y_start': int(data.get('y_start') or 0),
            'y_end': int(data.get('y_end') or 100),
            'threshold': float(data.get('threshold') or 5.0),
            'frame_interval_sec': float(data.get('frame_interval_sec') or 1.0)
        }

        print("Step 1: Downloading video...")
        video_path = download_youtube_video(youtube_url, temp_dir)
        if not video_path:
            raise ValueError("영상을 다운로드할 수 없습니다.")

        print("Step 2: Processing frames...")
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)

        processed_image_paths = process_video_frames(
            video_path, image_output_dir,
            start_time, end_time,
            config['x_start'], config['x_end'], config['y_start'], config['y_end'],
            config['threshold'], config['frame_interval_sec']
        )

        if not processed_image_paths:
            raise ValueError("추출된 악보 이미지가 없습니다. 설정값을 조절해 보세요.")

        if inspection_mode:
            # 검수 모드: 이미지 리스트를 만들지 않고 성공 응답만 보냄 (브라우저가 /inspect로 이동)
            return jsonify({
                'inspection_needed': True,
                'session_id': session_id
            })
        else:
            # 일반 모드: 즉시 PDF 생성 및 반환
            print("Step 3: Creating PDF (Immediate)...")
            pdf_io = create_pdf_from_images(processed_image_paths)
            return send_file(
                pdf_io, as_attachment=True,
                download_name='score.pdf', mimetype='application/pdf'
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        # 오류 시에는 세션 폴더 즉시 삭제
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

    finally:
        # 일반 모드일 때만 즉시 삭제 (검수 모드일 때는 GC가 처리하도록 함)
        if not inspection_mode and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleanup (Sync): {temp_dir}")


@app.route('/finalize', methods=['POST'])
def finalize():
    """검수 완료 후 선택된 이미지들로 PDF 생성"""
    try:
        data = request.json
        session_id = data.get('session_id')
        selected_files = data.get('selected_images')

        session_dir = os.path.join(TEMP_BASE_DIR, session_id)
        if not os.path.exists(session_dir):
            return jsonify({'error': '세션이 만료되었습니다. 다시 시도해 주세요.'}), 410

        image_paths = [os.path.join(session_dir, 'images', f) for f in selected_files]
        pdf_io = create_pdf_from_images(image_paths)

        # 파일 전송 후 삭제는 GC가 처리하도록 mtime만 갱신하거나
        # 혹은 여기서 명시적으로 삭제할 수 있으나 안전을 위해 GC에 위임
        return send_file(
            pdf_io, as_attachment=True,
            download_name='final_score.pdf', mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 1. 초기화 작업
    cleanup_temp_dir_startup()
    update_yt_dlp()

    # 2. 백그라운드 스레드들 실행
    start_periodic_update()
    threading.Thread(target=cleanup_worker, daemon=True).start()

    # 3. 서버 실행
    app.run(host='0.0.0.0', port=5000, debug=True)