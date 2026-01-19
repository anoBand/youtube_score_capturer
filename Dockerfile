# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# [수정] nodejs 추가
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p temp
EXPOSE 5000

CMD ["python", "app.py"]