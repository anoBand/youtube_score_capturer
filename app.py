# app.py

import os
import tempfile
import shutil
import traceback
import subprocess
import sys
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS

# 커스텀 모듈 임포트
from modules.youtube_downloader import download_1080p_video_only as download_youtube_video
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images


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


app = Flask(__name__)
CORS(app)

# 프로젝트 내 임시 저장 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(PROJECT_ROOT, 'temp')

# 서버 시작 시 임시 폴더가 없다면 생성
if not os.path.exists(TEMP_BASE_DIR):
    os.makedirs(TEMP_BASE_DIR)

update_yt_dlp()


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/execute', methods=['POST'])
def execute():
    # 각 요청마다 독립적인 임시 디렉터리 생성 (Race Condition 방지)
    temp_dir = tempfile.mkdtemp(dir=TEMP_BASE_DIR)
    print(f"Started request. Temporary directory: {temp_dir}")

    try:
        data = request.form
        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL이 필요합니다.'}), 400

        # 데이터 파싱 및 기본값 설정
        start_time = time_to_seconds(data.get('start_time'))
        end_time = time_to_seconds(data.get('end_time'))

        # UI에서 넘어온 문자열 데이터를 숫자로 변환
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
        if not video_path or not os.path.exists(video_path):
            raise ValueError("영상을 다운로드할 수 없습니다. URL이나 네트워크 상태를 확인하세요.")

        print("Step 2: Processing frames...")
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)

        processed_image_paths = process_video_frames(
            video_path,
            image_output_dir,
            start_time, end_time,
            config['x_start'], config['x_end'], config['y_start'], config['y_end'],
            config['threshold'],
            config['frame_interval_sec']
        )

        if not processed_image_paths:
            raise ValueError("추출된 악보 이미지가 없습니다. 설정값(Threshold 등)을 조절해 보세요.")

        print("Step 3: Creating PDF...")
        pdf_io = create_pdf_from_images(processed_image_paths)

        print("Step 4: Sending file...")
        return send_file(
            pdf_io,
            as_attachment=True,
            download_name='sheet_music_score.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        # 작업 완료 후 해당 요청의 임시 파일들만 삭제
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up directory: {temp_dir}")


if __name__ == '__main__':
    # 외부 접속을 허용하려면 host='0.0.0.0' 추가 고려
    app.run(debug=True, port=5000)