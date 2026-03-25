# Dockerfile

# 1. Python 환경 설정
FROM python:3.10-slim

# 2. 작업 디렉토리 생성
WORKDIR /app

# 3. 시스템 패키지 설치 (ffmpeg, libgl 등)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# 4. 파이썬 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade --no-cache-dir yt-dlp

# 5. 소스 코드 복사 및 임시 폴더 생성
COPY . .
RUN mkdir -p temp

# 6. 서비스 포트 및 실행 명령
EXPOSE 80
CMD ["python", "app.py"]