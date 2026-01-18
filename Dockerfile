# 주석: Dockerfile
FROM python:3.10-slim

# 필수 패키지 설치 (ffmpeg 등 영상 처리에 필요한 경우 추가)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 복사
COPY . .

# Flask/FastAPI 등의 앱이 실행될 포트 (예: 5000)
EXPOSE 5000

# 앱 실행 (app.py가 Flask인 경우 예시)
CMD ["python", "app.py"]