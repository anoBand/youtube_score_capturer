import yt_dlp
import os

def download_1080p_video_only(url, output_dir):
    # Downloads a YouTube video to the specified directory and returns the file path.
    
    # Configure yt-dlp options
    ydl_opts = {
        # 변경점 1: [height<=1080] 필터를 추가하여 최대 해상도를 1080p로 제한합니다.
        # 1080p 이하의 mp4 포맷을 우선으로 찾고, 없으면 다른 포맷이라도 1080p 이하 중 최상의 것을 선택합니다.
        'format': 'bestvideo[ext=mp4][height<=1080]/bestvideo[height<=1080]',
        
        # 변경점 2: 파일명을 'video.mp4'로 다시 고정합니다.
        'outtmpl': os.path.join(output_dir, 'video.mp4'),
        
        # 다운로드 중 덮어쓰기를 허용 (이미 video.mp4가 있을 경우)
        'overwrites': True,
        
        'quiet': True,
    }

    print(f"Starting 1080p video-only download for URL: {url} (No FFmpeg)")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    # 최종 추천 코드
        try:
            # 1. yt-dlp에게 다운로드를 지시합니다. ('outtmpl' 옵션에 따라 video.mp4로 저장됨)
            ydl.download([url])
            
            # 2. 저장 경로는 이미 'video.mp4'로 알고 있으므로 직접 만듭니다.
            downloaded_path = os.path.join(output_dir, 'video.mp4')
            
            print(f"Download complete. Video saved at: {downloaded_path}")
            
            # 3. 성공 경로를 반환합니다.
            return downloaded_path
            
        except Exception as e:
            # 오류 처리는 그대로 유지
            print(f"Error during download: {e}")
            raise ValueError(f"Failed to download YouTube video: {e}")