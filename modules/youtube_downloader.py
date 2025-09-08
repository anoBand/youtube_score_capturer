# modules/youtube_downloader.py (수동 쿠키 갱신을 위한 최종 안정화 버전)

import yt_dlp
import os

def download_1080p_video_only(url, output_dir):
    # 이 파일의 위치를 기준으로 프로젝트 루트 폴더를 찾습니다.
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 프로젝트 루트에 있는 cookies.txt 파일의 경로를 지정합니다.
    COOKIE_FILE = os.path.join(PROJECT_ROOT, 'cookies.txt')

    ydl_opts = {
        # 우리 애플리케이션에 최적화된 설정 (변경하지 않음)
        'format': 'bestvideo[ext=mp4][height<=1080]/bestvideo[height<=1080]',
        'outtmpl': os.path.join(output_dir, 'video.mp4'),
        'overwrites': True,
        'quiet': True,
        
        # 안정성을 위한 추가 옵션 (유지)
        'extractor_retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
        },
    }

    # 쿠키 파일이 존재할 경우에만 인증 옵션을 추가합니다.
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE
        print("✅ Authentication cookies found and will be used.")
    else:
        print("⚠️ Authentication cookies not found. Proceeding without authentication.")

    print(f"Starting video download for URL: {url}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            downloaded_path = os.path.join(output_dir, 'video.mp4')
            print(f"Download complete. Video saved at: {downloaded_path}")
            return downloaded_path
        except Exception as e:
            print(f"Error during download: {e}")