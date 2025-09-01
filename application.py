import os
import tempfile
import shutil
import traceback
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS

# 커스텀 모듈 임포트
from modules.youtube_downloader import download_youtube_video
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images

# Beanstalk은 'application'이라는 이름의 변수를 찾습니다.
application = Flask(__name__)
CORS(application)

@application.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html')

@application.route('/process', methods=['POST'])
def process_video():
    """YouTube URL을 받아 악보 추출 프로세스를 실행합니다."""
    # 요청으로부터 파라미터 추출
    params = request.form.to_dict()
    youtube_url = params.get('url')

    if not youtube_url:
        return jsonify({'error': 'YouTube URL이 필요합니다.'}), 400

    # 임시 디렉토리 생성 (요청마다 고유한 공간 사용)
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")

    try:
        # 1. 유튜브 영상 다운로드
        video_path = download_youtube_video(youtube_url, temp_dir)
        
        # 2. OpenCV로 영상 프레임 처리
        # output_dir을 temp_dir 아래에 지정하여 중간 이미지 저장
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(video_path, image_output_dir, params)
        
        if not processed_image_paths:
            raise ValueError("영상에서 악보 이미지를 추출하지 못했습니다.")

        # 3. PDF 생성
        pdf_path = create_pdf_from_images(processed_image_paths, temp_dir, filename="sheet_music.pdf")
        
        # 4. 생성된 PDF 파일 전송
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='sheet_music.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        # 에러 로깅
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        # 5. 모든 작업 완료 후 임시 디렉토리 정리
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == '__main__':
    # 로컬 테스트용 서버 실행
    application.run(host='0.0.0.0', port=5000, debug=True)
