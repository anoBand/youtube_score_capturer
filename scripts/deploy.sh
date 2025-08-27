#!/bin/bash
set -e

echo "🚀 YouTube Score Capturer 배포 시작..."

# 추가 저장소(EPEL) 활성화 (ffmpeg 설치를 위해)
echo "📦 추가 저장소(EPEL)를 활성화합니다..."
sudo amazon-linux-extras install epel -y

# 기본 패키지 업데이트 및 설치
echo "📦 패키지를 설치합니다..."
sudo yum update -y
sudo yum install -y python3-pip nginx ffmpeg curl htop

# 프로젝트 디렉토리로 이동
cd /home/ec2-user/youtube-score-capturer

# Python 가상환경 설정
echo "🐍 Python 가상환경 설정 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 임시 디렉토리 생성 및 권한 설정
mkdir -p temp
chmod 755 temp

# Systemd 서비스 설정
echo "⚙️ 서비스 설정 중..."
sudo cp config/systemd.service /etc/systemd/system/youtube-score.service
sudo systemctl daemon-reload
sudo systemctl enable youtube-score

# 서비스 재시작 (이미 실행 중이라면)
if sudo systemctl is-active --quiet youtube-score; then
    sudo systemctl restart youtube-score
else
    sudo systemctl start youtube-score
fi

# Nginx 설정
echo "🌐 웹서버 설정 중..."
sudo cp config/nginx.conf /etc/nginx/sites-available/youtube-score
sudo ln -sf /etc/nginx/sites-available/youtube-score /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx 설정 테스트 및 재시작
sudo nginx -t
sudo systemctl reload nginx

# 방화벽 설정
echo "🔒 방화벽 설정 중..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# 로그 디렉토리 생성
sudo mkdir -p /var/log/youtube-score
sudo chown ec2-user:ec2-user /var/log/youtube-score


echo "✅ 배포 완료!"
echo ""
echo "📊 서비스 상태:"
sudo systemctl status youtube-score --no-pager -l
echo ""
echo "🌐 외부 IP: $(curl -s ifconfig.me)"
echo "💻 브라우저에서 http://$(curl -s ifconfig.me) 접속하여 테스트하세요"
echo ""
echo "🔍 유용한 명령어:"
echo "  - 로그 보기: sudo journalctl -u youtube-score -f"
echo "  - 서비스 재시작: sudo systemctl restart youtube-score"
echo "  - Nginx 재시작: sudo systemctl reload nginx"
