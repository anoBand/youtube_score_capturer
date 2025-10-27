#modules/youtube_downloader.py
import yt_dlp
import os

def download_1080p_video_only(url, output_dir):

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=1080][vcodec^=avc1]/bestvideo[ext=mp4][height<=1080]',
        'outtmpl': os.path.join(output_dir, 'video.mp4'),
        'overwrites': True,
        'quiet': True,

        # 안정성을 위한 추가 옵션
        'extractor_retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
        },

    }

    print(f"Starting video download for URL: {url}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            downloaded_path = os.path.join(output_dir, 'video.mp4')
            print(f"Download complete. Video saved at: {downloaded_path}")
            return downloaded_path
        except Exception as e:
            print(f"Error during download: {e}")
            # 403 오류 등이 발생할 경우 None을 반환하도록 처리 (app.py의 오류 처리를 위해)
            return None