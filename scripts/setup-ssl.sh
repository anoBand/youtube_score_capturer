#!/bin/bash
# setup-ssl.sh - Let's Encrypt SSL 인증서 설정

echo "🔐 SSL 인증서 설정 시작..."
echo "================================================"

# 도메인 입력받기
read -p "도메인 이름 입력 (예: my-youtube-score.duckdns.org): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo "❌ 도메인 이름을 입력해주세요!"
    exit 1
fi

# 1. Certbot 설치
echo "📦 Certbot 설치 중..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 2. 도메인 접속 테스트
echo "🧪 도메인 접속 테스트 중..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN_NAME" || echo "failed")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "⚠️ 도메인이 아직 연결되지 않았습니다 (HTTP: $HTTP_STATUS)"
    echo "DNS 전파를 기다린 후 다시 시도해주세요."
    echo "몇 분 후 다음 명령어로 다시 실행하세요:"
    echo "./setup-ssl.sh"
    exit 1
fi

# 3. SSL 인증서 발급
echo "🔒 SSL 인증서 발급 중..."
sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email your-email@example.com

if [ $? -eq 0 ]; then
    echo "✅ SSL 인증서 발급 성공!"
else
    echo "❌ SSL 인증서 발급 실패"
    echo "수동으로 발급을 시도해보세요:"
    echo "sudo certbot --nginx -d $DOMAIN_NAME"
    exit 1
fi

# 4. 자동 갱신 설정
echo "🔄 SSL 인증서 자동 갱신 설정 중..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# 5. 강제 HTTPS 리다이렉트 확인
echo "🌐 HTTPS 리다이렉트 확인 중..."
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx 설정 업데이트 완료"
fi

# 6. HTTPS 접속 테스트
echo "🧪 HTTPS 접속 테스트 중..."
sleep 3
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN_NAME" || echo "failed")
if [ "$HTTPS_STATUS" = "200" ]; then
    echo "✅ HTTPS 접속 성공!"
elif [ "$HTTPS_STATUS" = "failed" ]; then
    echo "⚠️ HTTPS 접속 실패 - SSL 인증서 확인 필요"
else
    echo "⚠️ HTTPS 응답: $HTTPS_STATUS"
fi

echo ""
echo "🎉 SSL 설정 완료!"
echo "================================================"
echo "🔒 HTTPS URL: https://$DOMAIN_NAME"
echo "🔄 HTTP는 자동으로 HTTPS로 리다이렉트됩니다"
echo ""
echo "📋 관리 명령어:"
echo "   - SSL 상태 확인: sudo certbot certificates"
echo "   - 수동 갱신: sudo certbot renew"
echo "   - Nginx 재시작: sudo systemctl reload nginx"

# 7. SSL 정보 추가
CURRENT_USER=$(whoami)
if [ -f "/home/$CURRENT_USER/domain-info.txt" ]; then
    echo "" >> /home/$CURRENT_USER/domain-info.txt
    echo "=== SSL 인증서 정보 ===" >> /home/$CURRENT_USER/domain-info.txt
    echo "HTTPS URL: https://$DOMAIN_NAME" >> /home/$CURRENT_USER/domain-info.txt
    echo "SSL 발급일: $(date)" >> /home/$CURRENT_USER/domain-info.txt
    echo "자동 갱신: 매달 12일 12시" >> /home/$CURRENT_USER/domain-info.txt
fi