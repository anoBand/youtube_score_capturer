#!/bin/bash
set -e

echo "🔄 애플리케이션 업데이트 중..."

cd /home/ubuntu/youtube-score-capturer

# Git pull로 최신 코드 가져오기
echo "📥 최신 코드 다운로드 중..."
git pull origin main

# 가상환경 활성화 및 패키지 업데이트
echo "📦 패키지 업데이트 중..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 서비스 재시작
echo "🔄 서비스 재시작 중..."
sudo systemctl restart youtube-score

# 상태 확인
echo "✅ 업데이트 완료!"
sudo systemctl status youtube-score --no-pager -l
