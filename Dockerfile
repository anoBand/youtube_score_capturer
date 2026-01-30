FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 1. 고정된 requirements 설치
RUN pip install --no-cache-dir -r requirements.txt
# 2. yt-dlp만 별도로 최신 버전 강제 업데이트
RUN pip install --upgrade --no-cache-dir yt-dlp

COPY . .
RUN mkdir -p temp
EXPOSE 5000

CMD ["python", "app.py"]