import yt_dlp
import os

def download_youtube_video(url, output_dir):
    """유튜브 영상을 지정된 디렉토리에 다운로드하고 파일 경로를 반환합니다."""
    # yt-dlp 옵션 설정
    ydl_opts = {
        # 720p 이하의 mp4 포맷으로 다운로드하여 메모리 및 처리 시간 절약
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, 'video.mp4'), # 파일명 고정
        'quiet': True, # 로그 최소화
    }
    
    print(f"Starting download for URL: {url}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            # 다운로드된 파일의 실제 경로를 반환
            filename = ydl.prepare_filename(info)
            # 확장자가 .mp4가 아닐 경우를 대비해 고정된 이름 사용
            downloaded_path = os.path.join(output_dir, 'video.mp4')
            print(f"Download complete. Video saved at: {downloaded_path}")
            return downloaded_path
        except Exception as e:
            print(f"Error during download: {e}")
            raise ValueError(f"유튜브 영상 다운로드에 실패했습니다: {e}")
