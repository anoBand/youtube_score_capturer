# modules/youtube_downloader.py
import os
import sys
import subprocess
import io
import cv2


def get_bin_path(bin_name):
    """ PyInstaller 번들 내부의 bin 폴더에서 실행 파일 경로 반환 """
    if sys.platform == "win32":
        bin_name += ".exe"

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'bin', bin_name)
    return os.path.join(os.path.abspath("."), 'bin', bin_name)


def get_startup_info():
    """ 윈도우에서 서브프로세스 실행 시 콘솔 창이 뜨지 않도록 설정 """
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def get_video_stream_url(url):
    """ yt-dlp를 사용하여 영상 스트림 URL을 가져옵니다. (사용자 IP 사용) """
    ytdlp_path = get_bin_path('yt-dlp')
    startup_info = get_startup_info()

    try:
        cmd = [ytdlp_path, "-g", "-f", "bestvideo", url]
        # startupinfo 옵션 추가
        result = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return result.strip()
    except Exception as e:
        print(f"Error fetching stream URL: {e}")
        return None


def get_single_frame_as_bytes(stream_url, seconds):
    """ OpenCV를 사용하여 특정 시점의 프레임을 캡처합니다. """
    cap = cv2.VideoCapture(stream_url)
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    success, frame = cap.read()
    if success:
        _, buffer = cv2.imencode('.jpg', frame)
        cap.release()
        return io.BytesIO(buffer)
    cap.release()
    return None


def download_youtube_video(url, download_dir):
    """ 영상을 로컬 임시 폴더로 다운로드합니다. """
    ytdlp_path = get_bin_path('yt-dlp')
    ffmpeg_path = get_bin_path('ffmpeg')
    output_template = os.path.join(download_dir, 'video.%(ext)s')
    startup_info = get_startup_info()

    try:
        # ffmpeg-location을 지정하여 빌드 내부의 ffmpeg를 사용하게 함
        cmd = [
            ytdlp_path,
            "-f", "bestvideo",
            "--ffmpeg-location", os.path.dirname(ffmpeg_path),
            "-o", output_template,
            url
        ]

        # startupinfo 옵션 추가
        subprocess.check_call(
            cmd,
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        # 실제 생성된 파일명 찾기
        for f in os.listdir(download_dir):
            if f.startswith('video'):
                return os.path.join(download_dir, f)
        return None
    except Exception as e:
        print(f"Download Error: {e}")
        return None