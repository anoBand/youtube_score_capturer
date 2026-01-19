# 1. 파이썬 3.10 슬림 버전 사용
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필수 시스템 패키지 설치 [수정됨]
# - libgl1-mesa-glx -> libgl1 으로 변경
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 프로젝트 파일 복사
COPY . .

# 6. 임시 폴더 생성
RUN mkdir -p temp

# 7. 포트 개방
EXPOSE 5000

# 8. 앱 실행
CMD ["python", "app.py"]