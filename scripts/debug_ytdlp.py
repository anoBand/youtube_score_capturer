# debug_ytdlp.py
# 로컬/서버 배포 환경에서의 yt-dlp 및 멀티미디어 환경 진단 스크립트

import sys
import os
import subprocess
import yt_dlp
import traceback

# 테스트용 URL (공개된 고화질 영상)
TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def check_command(cmd):
    """시스템 명령어가 실행 가능한지 확인"""
    try:
        subprocess.run([cmd, '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


def debug_yt_environment():
    print("=" * 60)
    print(f"🔍 System & Library Diagnostics")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"📺 yt-dlp Version: {yt_dlp.version.__version__}")

    # FFmpeg 확인 (악보 캡처 앱의 핵심 의존성)
    ffmpeg_ok = check_command('ffmpeg')
    ffprobe_ok = check_command('ffprobe')
    print(f"🎬 FFmpeg Installed: {'✅ Yes' if ffmpeg_ok else '❌ No'}")
    print(f"🔎 FFprobe Installed: {'✅ Yes' if ffprobe_ok else '❌ No'}")

    # 쿠키 파일 감지
    cookie_file = '/app/cookies.txt'
    has_cookies = os.path.exists(cookie_file)
    print(f"🍪 cookies.txt Found: {'✅ Yes (Auto-loading)' if has_cookies else 'ℹ️  No (Using guest mode)'}")
    print("=" * 60)

    ydl_opts = {
        'format': 'best',
        'quiet': False,
        'verbose': True,
        'no_warnings': False,
        'socket_timeout': 15,
        'nocheckcertificate': True,

        # [핵심] 이 줄을 추가해야 로컬에 설치된 Node.js를 인식합니다!
        'js_runtimes': {'node': {}, 'deno': {}},
        # [★추가] 외부 챌린지 해결 스크립트 다운로드 허용
        'remote_components': {'ejs': 'github'},
    }
    # 쿠키가 존재할 경우에만 경로 추가
    if has_cookies:
        ydl_opts['cookiefile'] = cookie_file

    print(f"🚀 Testing YouTube Access: {TEST_URL}")
    print("-" * 60)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. 메타데이터 및 스트림 정보 추출
            info = ydl.extract_info(TEST_URL, download=False)

            print("-" * 60)
            print("✅ CONNECTION SUCCESS!")
            print(f"📹 Title: {info.get('title')}")
            print(f"📊 Channel: {info.get('uploader')}")
            print(f"🎞️  Selected Format: {info.get('format_id')} ({info.get('resolution')})")

            # 스트림 URL 존재 여부 확인
            stream_url = info.get('url')
            if stream_url:
                print(f"🔗 Stream URL Found (Length: {len(stream_url)} chars)")
                print(f"🌐 URL Preview: {stream_url[:70]}...")
            else:
                print("⚠️  Warning: Metadata fetched, but direct stream URL is missing.")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        print("-" * 60)
        print("❌ DOWNLOAD ERROR")
        print(f"Message: {error_msg}")

        print("\n[Diagnostic Guide]")
        if "429" in error_msg:
            print("👉 Rate Limited: 요청이 너무 많습니다. IP가 일시적으로 제한되었습니다.")
        elif "403" in error_msg or "Sign in" in error_msg:
            print("👉 Access Denied: 유튜브가 이 환경을 봇으로 의심합니다. 쿠키가 필요할 수 있습니다.")
        elif "format" in error_msg:
            print("👉 Format Error: 요청한 화질 옵션이 해당 영상에 존재하지 않습니다.")
        else:
            print("👉 Network/IP Issue: 네트워크 연결이나 ISP의 유튜브 접속 제한을 확인하세요.")

    except Exception as e:
        print("-" * 60)
        print("❌ UNEXPECTED SYSTEM ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    debug_yt_environment()