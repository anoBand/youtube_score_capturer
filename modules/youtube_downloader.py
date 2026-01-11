# modules/youtube_downloader.py

import yt_dlp
import os


def download_1080p_video_only(url, output_dir):
    # 다운로드 결과 파일 경로 설정
    output_path = os.path.join(output_dir, 'video.mp4')

    ydl_opts = {
        # [기존 유지] 1080p 이하 mp4(avc1) 우선 선택
        'format': 'bestvideo[ext=mp4][height<=1080][vcodec^=avc1]/bestvideo[ext=mp4][height<=1080]',
        'outtmpl': output_path,
        'overwrites': True,
        'quiet': True,
        'no_warnings': True,

        # [개선] 웹 서비스 안정성을 위한 추가 설정
        'extractor_retries': 3,
        'socket_timeout': 30,  # 30초 동안 응답 없으면 타임아웃
        'nocheckcertificate': True,  # SSL 인증서 검증 생략 (서버 환경 호환성)
        'no_mtime': True,  # 파일 수정 시간을 유튜브 업로드 시간으로 맞추지 않음

        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        },
    }

    print(f"📥 Downloading video: {url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 추출 전 정보 확인 (URL 유효성 체크)
            # info = ydl.extract_info(url, download=True)
            ydl.download([url])

        if os.path.exists(output_path):
            print(f"✅ Download success: {output_path}")
            return output_path
        else:
            print("❌ Download failed: File not found after process.")
            return None

    except yt_dlp.utils.DownloadError as de:
        print(f"❌ YouTube Download Error: {str(de)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error during download: {str(e)}")
        return None
