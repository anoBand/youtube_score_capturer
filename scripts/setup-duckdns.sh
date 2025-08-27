#!/bin/bash
# setup-duckdns.sh - DuckDNS 무료 도메인 설정

echo "🦆 DuckDNS 무료 도메인 설정 시작..."
echo "================================================"

# 사용자 입력 받기
read -p "DuckDNS 도메인 이름 입력 (예: my-youtube-score): " DOMAIN_NAME
read -p "DuckDNS 토큰 입력 (DuckDNS 사이트에서 확인): " DUCK_TOKEN

if [ -z "$DOMAIN_NAME" ] || [ -z "$DUCK_TOKEN" ]; then
    echo "❌ 도메인 이름과 토큰을 모두 입력해주세요!"
    exit 1
fi

FULL_DOMAIN="${DOMAIN_NAME}.duckdns.org"
CURRENT_USER=$(whoami)

echo "설정할 도메인: $FULL_DOMAIN"
echo ""

# 1. 현재 IP 확인
CURRENT_IP=$(curl -s http://checkip.amazonaws.com)
echo "🌐 현재 외부 IP: $CURRENT_IP"

# 2. DuckDNS IP 업데이트
echo "🔄 DuckDNS에 IP 등록 중..."
UPDATE_RESULT=$(curl -s "https://www.duckdns.org/update?domains=${DOMAIN_NAME}&token=${DUCK_TOKEN}&ip=${CURRENT_IP}")

if [ "$UPDATE_RESULT" = "OK" ]; then
    echo "✅ DuckDNS IP 등록 성공!"
else
    echo "❌ DuckDNS IP 등록 실패: $UPDATE_RESULT"
    echo "토큰과 도메인 이름을 다시 확인해주세요."
    exit 1
fi

# 3. DNS 확인 (몇 초 기다린 후)
echo "⏳ DNS 전파 대기 중..."
sleep 10

# 4. DuckDNS 자동 업데이트 스크립트 생성
echo "🤖 자동 업데이트 스크립트 생성 중..."
mkdir -p /home/$CURRENT_USER/duckdns

cat > /home/$CURRENT_USER/duckdns/duck.sh << EOF
#!/bin/bash
# DuckDNS 자동 업데이트 스크립트

CURRENT_IP=\$(curl -s http://checkip.amazonaws.com)
UPDATE_RESULT=\$(curl -s "https://www.duckdns.org/update?domains=${DOMAIN_NAME}&token=${DUCK_TOKEN}&ip=\$CURRENT_IP")

if [ "\$UPDATE_RESULT" = "OK" ]; then
    echo "\$(date): ✅ DuckDNS IP 업데이트 성공: \$CURRENT_IP" >> /home/$CURRENT_USER/duckdns/duck.log
else
    echo "\$(date): ❌ DuckDNS IP 업데이트 실패: \$UPDATE_RESULT" >> /home/$CURRENT_USER/duckdns/duck.log
fi
EOF

chmod +x /home/$CURRENT_USER/duckdns/duck.sh

# 5. Cron 작업 추가 (5분마다 IP 확인)
echo "⏰ 자동 업데이트 Cron 작업 추가 중..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/$CURRENT_USER/duckdns/duck.sh") | crontab -

# 6. Nginx 설정 업데이트
echo "🌐 Nginx 설정 업데이트 중..."
sudo tee /etc/nginx/sites-available/youtube-score > /dev/null << EOF
server {
    listen 80;
    server_name $FULL_DOMAIN;

    client_max_body_size 100M;
    client_body_timeout 300s;
    
    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 긴 처리 시간을 위한 타임아웃 설정
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
    
    # 정적 파일 서빙
    location /static {
        alias /home/$CURRENT_USER/youtube-score-capturer/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 파비콘 404 방지
    location /favicon.ico {
        access_log off;
        log_not_found off;
        return 204;
    }
}
EOF

# 7. Nginx 설정 테스트 및 재시작
echo "🔄 Nginx 재시작 중..."
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    echo "✅ Nginx 설정 업데이트 완료"
else
    echo "❌ Nginx 설정 오류 발생"
    exit 1
fi

# 8. 도메인 접속 테스트
echo "🧪 도메인 접속 테스트 중..."
sleep 5

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$FULL_DOMAIN" || echo "failed")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ 도메인 접속 성공!"
elif [ "$HTTP_STATUS" = "failed" ]; then
    echo "⏳ DNS 전파 중일 수 있습니다. 몇 분 후 다시 시도해보세요."
else
    echo "⚠️ HTTP 응답: $HTTP_STATUS (DNS 전파 대기 중일 수 있음)"
fi

echo ""
echo "🎉 DuckDNS 설정 완료!"
echo "================================================"
echo "🌐 접속 URL: http://$FULL_DOMAIN"
echo "📋 관리 정보:"
echo "   - DuckDNS 관리: https://duckdns.org"
echo "   - 로그 파일: /home/$CURRENT_USER/duckdns/duck.log"
echo "   - 업데이트 스크립트: /home/$CURRENT_USER/duckdns/duck.sh"
echo ""
echo "💡 팁: DNS 전파까지 최대 15분 정도 걸릴 수 있습니다."
echo "만약 접속이 안 된다면 잠시 후 다시 시도해보세요!"

# 9. 접속 정보 저장
cat > /home/$CURRENT_USER/domain-info.txt << EOF
=== YouTube Score Capturer 도메인 정보 ===
도메인: $FULL_DOMAIN
생성일: $(date)
DuckDNS 토큰: $DUCK_TOKEN
현재 IP: $CURRENT_IP

관리 명령어:
- DuckDNS 수동 업데이트: /home/$CURRENT_USER/duckdns/duck.sh
- DuckDNS 로그 확인: tail -f /home/$CURRENT_USER/duckdns/duck.log
- Nginx 재시작: sudo systemctl reload nginx
EOF

echo "📄 도메인 정보가 domain-info.txt에 저장되었습니다."