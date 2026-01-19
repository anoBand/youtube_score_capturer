# 1. 파이썬 3.10 슬림 버전 사용 (가볍고 안정적)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필수 시스템 패키지 설치 (이 부분이 가장 중요합니다!)
# - ffmpeg: yt-dlp 영상/오디오 병합용
# - libgl1-mesa-glx, libglib2.0-0: OpenCV 작동용 (없으면 ImportError 발생)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 및 설치
# (캐시 효율을 위해 requirements.txt만 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 프로젝트 파일 복사
COPY . .

# 6. 임시 폴더 생성 (앱 로직상 필요)
RUN mkdir -p temp

# 7. 포트 개방
EXPOSE 5000

# 8. 앱 실행
# (프로덕션 환경에서는 gunicorn 권장하지만, 기존 app.py 실행 방식 유지)
CMD ["python", "app.py"]