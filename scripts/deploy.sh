	#!/bin/bash
set -e

echo "🚀 YouTube Score Capturer 배포 시작..."

# --- ffmpeg: 독립 실행 버전 직접 설치 (수정된 버전) ---
echo "📦 ffmpeg 설치를 시작합니다 (독립 실행 버전 다운로드 방식)..."

# 1. 최신 ffmpeg git 빌드 다운로드 (-L 옵션으로 리다이렉트 자동 처리)
curl -L -o ffmpeg-git.tar.xz https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz

# 2. 다운로드한 파일 압축 해제
tar -xf ffmpeg-git.tar.xz

# 3. 압축 해제된 폴더 안의 실행 파일을 시스템 경로로 이동
sudo mv ffmpeg-git-*-amd64-static/ffmpeg /usr/local/bin/
sudo mv ffmpeg-git-*-amd64-static/ffprobe /usr/local/bin/

# 4. 정리: 다운로드한 압축 파일과 압축 해제된 폴더 삭제
rm -rf ffmpeg-git-*-amd64-static
rm ffmpeg-git.tar.xz

echo "✅ ffmpeg 설치 완료."
ffmpeg -version # 설치 확인

# --- 나머지 패키지 설치 ---
echo "📦 나머지 패키지를 설치합니다..."
sudo yum update -y
sudo yum install -y python3-pip nginx htop

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
# 아마존 리눅스 방식: /etc/nginx/conf.d/ 폴더에 .conf 파일로 복사
sudo cp config/nginx.conf /etc/nginx/conf.d/youtube-score.conf

# Nginx 설정 테스트
sudo nginx -t

# Nginx 서비스 활성화 및 재시작
sudo systemctl enable nginx
sudo systemctl restart nginx

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
