#!/bin/bash
# fix-user-error.sh - AWS EC2 사용자 오류 수정

echo "🔧 AWS EC2 사용자 오류 수정 중..."

# 1. 현재 사용자 확인
CURRENT_USER=$(whoami)
echo "현재 사용자: $CURRENT_USER"

# 2. 서비스 중단
echo "서비스 중단 중..."
sudo systemctl stop youtube-score

# 3. systemd 서비스 파일 수정
echo "systemd 서비스 파일 수정 중..."
sudo tee /etc/systemd/system/youtube-score.service > /dev/null << EOF
[Unit]
Description=YouTube Score Capturer
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=/home/$CURRENT_USER/youtube-score-capturer
Environment=PATH=/home/$CURRENT_USER/youtube-score-capturer/venv/bin
Environment=FLASK_ENV=production
ExecStart=/home/$CURRENT_USER/youtube-score-capturer/venv/bin/python -m waitress --listen=127.0.0.1:5000 app:app
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 4. config 폴더의 systemd.service 파일도 수정
if [ -f "/home/$CURRENT_USER/youtube-score-capturer/config/systemd.service" ]; then
    echo "config/systemd.service 파일도 수정 중..."
    cat > /home/$CURRENT_USER/youtube-score-capturer/config/systemd.service << EOF
[Unit]
Description=YouTube Score Capturer
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=/home/$CURRENT_USER/youtube-score-capturer
Environment=PATH=/home/$CURRENT_USER/youtube-score-capturer/venv/bin
Environment=FLASK_ENV=production
ExecStart=/home/$CURRENT_USER/youtube-score-capturer/venv/bin/python -m waitress --listen=127.0.0.1:5000 app:app
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
fi

# 5. systemd 데몬 리로드
echo "systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 6. 가상환경이 제대로 설정되어 있는지 확인
cd /home/$CURRENT_USER/youtube-score-capturer
if [ ! -d "venv" ]; then
    echo "가상환경이 없습니다. 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "가상환경 확인됨"
fi

# 7. app.py 파일이 있는지 확인
if [ ! -f "app.py" ]; then
    echo "❌ app.py 파일이 없습니다!"
    echo "현재 디렉토리 내용:"
    ls -la
    exit 1
else
    echo "✅ app.py 파일 확인됨"
fi

# 8. 권한 설정
echo "파일 권한 설정 중..."
chown -R $CURRENT_USER:$CURRENT_USER /home/$CURRENT_USER/youtube-score-capturer

# 9. 서비스 시작
echo "서비스 시작 중..."
sudo systemctl start youtube-score

# 10. 상태 확인
sleep 3
echo ""
echo "📊 서비스 상태:"
sudo systemctl status youtube-score --no-pager -l

echo ""
echo "🔍 포트 확인:"
sudo netstat -tlnp | grep :5000

echo ""
echo "📋 최근 로그:"
sudo journalctl -u youtube-score --no-pager -n 10