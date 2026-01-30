# debug_ytdlp.py
# 로컬 및 서버 환경 통합 진단 스크립트 (v2.0)

import sys
import os
import subprocess
import traceback
import importlib


def check_command(cmd):
    """시스템 명령어(ffmpeg, node, deno 등) 존재 여부 확인"""
    try:
        # --version 대신 help나 단순 실행으로 체크 (일부 환경 대응)
        subprocess.run([cmd, '-v' if cmd == 'node' else '--version'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, PermissionError):
        return False


def update_yt_dlp():
    """yt-dlp 라이브러리를 최신 버전으로 업데이트"""
    print("🔄 Updating yt-dlp to latest stable...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'],
                       check=True, capture_output=True, text=True)
        print("✅ Update complete.")
    except Exception as e:
        print(f"⚠️ Update failed (skipping): {e}")


def debug_yt_environment():
    update_yt_dlp()

    # 모듈 재로드 (업데이트 후 버전 반영)
    import yt_dlp
    importlib.reload(yt_dlp)

    print("\n" + "=" * 60)
    print(f"🔍 [System Diagnostics]")
    print(f"🐍 Python:  {sys.version.split()[0]}")
    print(f"📺 yt-dlp:  {yt_dlp.version.__version__}")

    # 핵심 의존성 체크
    deps = {
        'FFmpeg': 'ffmpeg',
        'Node.js': 'node',
        'Deno': 'deno'
    }
    for name, cmd in deps.items():
        status = "✅ Found" if check_command(cmd) else "❌ Not Found"
        print(f"🛠️  {name:7}: {status}")

    # 쿠키 파일 확인
    cookie_file = 'cookies.txt'
    has_cookies = os.path.exists(cookie_file)
    print(f"🍪 Cookies: {'✅ cookies.txt loaded' if has_cookies else 'ℹ️  Guest Mode (No cookies.txt)'}")
    print("=" * 60 + "\n")

    MY_PO_TOKEN = "web+여기에_복사한_poToken_전체"
    MY_VISITOR_DATA = "여기에_복사한_visitorData"

    # [핵심 옵션 최적화]
    ydl_opts = {
        'format': 'best',
        'quiet': False,
        'verbose': True,  # 상세 로그 유지 (디버깅용)
        'no_warnings': False,
        'nocheckcertificate': True,

        # JS 런타임: 설치된 것이 있다면 자동으로 선택함
        'js_runtimes': {'deno': {}, 'node': {}},

        # 외부 챌린지 해결 스크립트 (최신 봇 탐지 우회 필수)
        'remote_components': ['ejs:github'],

        # 쿠키 설정
        'cookiefile': cookie_file if has_cookies else None,

        # PO Token: Deno/Node가 자동으로 생성하도록 빈 값 유지
        'extractor_args': {
            'youtube': {
                'po_token': [],
            }
        },
    }

    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    print(f"🚀 Testing YouTube Access: {test_url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

            print("\n" + "-" * 60)
            print("✅ CONNECTION SUCCESS!")
            print(f"📹 Title:   {info.get('title')}")
            print(f"📊 Channel: {info.get('uploader')}")
            print(f"🎞️  Format:  {info.get('format_id')} ({info.get('resolution')})")

            if info.get('url'):
                print("🔗 Stream URL generated successfully.")
            else:
                print("⚠️  Metadata fetched, but no direct stream URL found.")

    except Exception as e:
        print("\n" + "-" * 60)
        print("❌ CRITICAL ERROR")
        if "403" in str(e) or "bot" in str(e).lower():
            print("👉 YouTube blocked this request. Check your cookies.txt or Server IP.")
        elif "Node" in str(e) or "Deno" in str(e):
            print("👉 JavaScript Runtime issue. Install Node.js or Deno on your server.")
        else:
            traceback.print_exc()


if __name__ == "__main__":
    debug_yt_environment()