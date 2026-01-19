# debug_ytdlp.py
# 오라클 서버 배포 시 yt-dlp 접속 테스트 및 디버깅용 스크립트

import sys
import yt_dlp
import traceback

# 테스트할 안전한 유튜브 URL (저작권 문제없는 비디오 권장)
TEST_URL = "https://www.youtube.com/watch?v=onEiVpnKPIw"


def debug_yt_connection():
    print("=" * 60)
    print(f"🔍 yt-dlp Connection Debugger")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"📺 yt-dlp Version: {yt_dlp.version.__version__}")
    print("=" * 60)

    # modules/youtube_downloader.py 와 동일한 옵션 구성
    ydl_opts = {
        'format': 'best',
        'quiet': False,  # 디버깅을 위해 출력 켬
        'verbose': True,  # [중요] 상세 로그 출력 (서버 요청/응답 헤더 확인용)
        'no_warnings': False,

        # [추가] 쿠키 파일 경로 지정 (도커 내부 경로 기준)
        'cookiefile': 'cookies.txt',

        'extractor_args': {
            'youtube': {
                'player_client': ['ios'],  # 안드로이드를 1순위로 시도
            }
        },
    }

    print(f"🚀 Trying to fetch info from: {TEST_URL} as iOS Client")
    print("-" * 60)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)

            print("-" * 60)
            print("✅ SUCCESS! Connected as iOS.")
            print(f"📹 Title: {info.get('title')}")
            if info.get('url'):
                print(f"🌐 Stream URL Found: Yes")
            else:
                print("⚠️  No direct URL found (Formats might be hidden)")

    except Exception as e:
        print("-" * 60)
        print("❌ ERROR")
        print(e)
        traceback.print_exc()


if __name__ == "__main__":
    debug_yt_connection()