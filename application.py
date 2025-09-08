# application.py

import os
import tempfile
import shutil
import traceback
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS

from werkzeug.middleware.proxy_fix import ProxyFix

# --- 변경점 1: FFmpeg 없는 다운로더 함수를 임포트 ---
# (함수 이름은 최종 결정한 이름으로 맞춰주세요. 예: download_1080p_video_only)
from modules.youtube_downloader import download_1080p_video_only as download_youtube_video
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images


# Beanstalk looks for a variable named 'application'.
application = Flask(__name__)
# --- 변경점 2: ProxyFix 미들웨어 적용 ---
# 이 코드는 Beanstalk의 로드 밸런서 뒤에서 실행될 때,
# Flask가 X-Forwarded-Proto 같은 헤더를 신뢰하여 HTTPS 환경임을 인지하게 만듭니다.
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

CORS(application)

# Define a base temp directory within the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(PROJECT_ROOT, 'temp')

@application.route('/')
def index():
    # Renders the main page.
    return render_template('index.html')

def time_to_seconds(time_str):
    """Converts time string in HH:MM:SS or MM:SS to seconds."""
    if not time_str:
        return None
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]
    except (ValueError, IndexError):
        return None

@application.route('/execute', methods=['POST'])
def execute():
    if os.path.exists(TEMP_BASE_DIR):
        shutil.rmtree(TEMP_BASE_DIR)
    os.makedirs(TEMP_BASE_DIR)
    
    temp_dir = tempfile.mkdtemp(dir=TEMP_BASE_DIR)
    print(f"Created temporary directory: {temp_dir}")

    try:
        data = request.form
        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required.'}), 400

        start_time = time_to_seconds(data.get('start_time'))
        end_time = time_to_seconds(data.get('end_time'))
        
        x_start = int(data.get('x_start') or 0)
        x_end = int(data.get('x_end') or 100)
        y_start = int(data.get('y_start') or 0)
        y_end = int(data.get('y_end') or 100)
        threshold = float(data.get('threshold') or 5.0)
        transition_sec = float(data.get('transition_sec') or 2.0)
        frame_interval_sec = float(data.get('frame_interval_sec') or 1.0)

        # --- 변경점 2: 다운로더 호출 시 start_time, end_time 제거 ---
        # 이제 동영상 전체를 다운로드합니다.
        print("Step 1: Downloading full video (up to 1080p, no-ffmpeg)...")
        video_path = download_youtube_video(youtube_url, temp_dir)
        
        # --- 변경점 3: 이미지 프로세서 호출 시 start_time, end_time 추가 ---
        # 다운로드된 전체 영상에서 필요한 부분만 처리합니다.
        print("Step 2: Processing frames within the specified time range...")
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(
            video_path, 
            image_output_dir, 
            start_time, # 역할이 여기로 이동
            end_time,   # 역할이 여기로 이동
            x_start, x_end, y_start, y_end, 
            threshold, transition_sec, frame_interval_sec
        )
        
        if not processed_image_paths:
            raise ValueError("Could not extract sheet music images from the video.")

        print("Step 3: Creating PDF...")
        pdf_io = create_pdf_from_images(processed_image_paths)
        
        print("Step 4: Sending PDF file...")
        return send_file(
            pdf_io,
            as_attachment=True,
            download_name='sheet_music.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=True)