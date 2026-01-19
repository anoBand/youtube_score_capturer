# debug_ytdlp.py
# 오라클 서버 배포 시 yt-dlp 접속 테스트 및 디버깅용 스크립트

import sys
import yt_dlp
import traceback

# 테스트할 안전한 유튜브 URL (저작권 문제없는 비디오 권장)
TEST_URL = "https://www.youtube.com/watch?v=BaW_jenozKc"  # YouTube Help 채널 영상


def debug_yt_connection():
    print("=" * 60)
    print(f"🔍 yt-dlp Connection Debugger")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"📺 yt-dlp Version: {yt_dlp.version.__version__}")
    print("=" * 60)

    # modules/youtube_downloader.py 와 동일한 옵션 구성
    ydl_opts = {
        'format': 'bestvideo[height<=480][ext=mp4]/bestvideo[height<=480]',
        'quiet': False,  # 디버깅을 위해 출력 켬
        'verbose': True,  # [중요] 상세 로그 출력 (서버 요청/응답 헤더 확인용)
        'no_warnings': False,

        # 네트워크 안정성 옵션
        'socket_timeout': 10,
        'nocheckcertificate': True,

        # 브라우저 위장 헤더 (User-Agent)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        },
    }

    print(f"🚀 Trying to fetch info from: {TEST_URL}")
    print("⏳ Processing... (This might take a few seconds)")
    print("-" * 60)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1단계: 정보 추출 테스트 (다운로드 X)
            info = ydl.extract_info(TEST_URL, download=False)

            print("-" * 60)
            print("✅ SUCCESS! Successfully connected to YouTube.")
            print(f"📹 Title: {info.get('title')}")
            print(f"⏱️  Duration: {info.get('duration')}s")
            print(f"🔗 Stream URL extracted: {'Yes' if info.get('url') else 'No'}")

            # 실제 스트림 URL이 유효한지 확인
            if info.get('url'):
                print(f"🌐 Stream URL (Preview): {info.get('url')[:50]}...")
            else:
                print("⚠️  Warning: Metadata fetched, but no direct stream URL found.")

    except yt_dlp.utils.DownloadError as e:
        print("-" * 60)
        print("❌ DOWNLOAD ERROR (Connection Failed)")
        print(f"Error Message: {e}")
        print("\n[진단 가이드]")
        if "HTTP Error 429" in str(e):
            print("👉 원인: 너무 많은 요청 (Rate Limit). 잠시 후 다시 시도하세요.")
        elif "HTTP Error 403" in str(e) or "Sign in" in str(e):
            print("👉 원인: IP 차단됨 (Oracle Cloud IP가 막힘).")
            print("👉 해결: Cookies 파일(cookies.txt)을 추출하여 서버에 업로드하고 옵션에 추가해야 합니다.")

    except Exception as e:
        print("-" * 60)
        print("❌ UNEXPECTED ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    debug_yt_connection()