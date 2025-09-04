import yt_dlp
import os

def download_youtube_video(url, output_dir):
    # Downloads a YouTube video to the specified directory and returns the file path.
    # Configure yt-dlp options
    ydl_opts = {
        # Download in mp4 format, 720p or less, to save memory and processing time
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, 'video.mp4'), # Fixed filename
        'quiet': True, # Minimize logs
    }
    
    print(f"Starting download for URL: {url}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            # Return the actual path of the downloaded file
            filename = ydl.prepare_filename(info)
            # Use a fixed name in case the extension is not .mp4
            downloaded_path = os.path.join(output_dir, 'video.mp4')
            print(f"Download complete. Video saved at: {downloaded_path}")
            return downloaded_path
        except Exception as e:
            print(f"Error during download: {e}")
            raise ValueError(f"Failed to download YouTube video: {e}")