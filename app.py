# app.py

import os
import tempfile
import shutil
import traceback
import subprocess  # 1. subprocess 임포트
import sys         # 2. sys 임포트
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS
from modules.youtube_downloader import download_1080p_video_only as download_youtube_video
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images

def update_yt_dlp():
    """Checks and updates yt-dlp to the latest version using pip."""
    print("Checking for yt-dlp updates...")
    try:
        # sys.executable은 현재 실행 중인 파이썬의 경로 (venv 안의 파이썬)
        # --upgrade 옵션은 최신 버전이 아닐 때만 설치를 진행함
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL, # 성공 메시지는 숨김
            stderr=subprocess.DEVNULL  # 오류 메시지도 숨김 (네트워크 오류 등)
        )
        print("✅ yt-dlp is up-to-date.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to update yt-dlp: {e}")
    except Exception as e:
        print(f"⚠️ An error occurred during yt-dlp update check: {e}")

# Flask app object
app = Flask(__name__)
CORS(app)

update_yt_dlp()

# Define a base temp directory within the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(PROJECT_ROOT, 'temp')

@app.route('/')
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

@app.route('/execute', methods=['POST'])
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

        print("Step 1: Downloading full video (up to 1080p, no-ffmpeg)...")
        video_path = download_youtube_video(youtube_url, temp_dir)
        if not video_path or not os.path.exists(video_path):
            raise ValueError("Failed to download video. Please check the URL and network.")
        
        print("Step 2: Processing frames within the specified time range...")
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(
            video_path,
            image_output_dir,
            start_time, end_time,
            x_start, x_end, y_start, y_end,
            threshold,
            frame_interval_sec
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
    app.run(debug=True)
