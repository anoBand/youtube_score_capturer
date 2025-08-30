#!/bin/bash
# troubleshoot.sh - AWS EC2 웹 서비스 문제 해결 스크립트

echo "🔍 YouTube Score Capturer 문제 해결 진단 중..."
echo "================================================"

# 1. 외부 IP 확인
echo "🌐 외부 IP 주소:"
EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com)
echo "   $EXTERNAL_IP"
echo "   브라우저에서 접속: http://$EXTERNAL_IP"
echo ""

# 2. 서비스 상태 확인
echo "⚙️ 서비스 상태:"
echo "   YouTube Score 서비스:"
if systemctl is-active --quiet youtube-score; then
    echo "   ✅ 실행 중"
else
    echo "   ❌ 중단됨"
    echo "   재시작 중..."
    sudo systemctl restart youtube-score
fi

echo "   Nginx 서비스:"
if systemctl is-active --quiet nginx; then
    echo "   ✅ 실행 중"
else
    echo "   ❌ 중단됨"
    echo "   재시작 중..."
    sudo systemctl restart nginx
fi
echo ""

# 3. 포트 확인
echo "🔌 포트 상태:"
if sudo netstat -tlnp | grep -q ":80"; then
    echo "   ✅ 포트 80 열림"
    sudo netstat -tlnp | grep ":80"
else
    echo "   ❌ 포트 80 닫힘"
fi

if sudo netstat -tlnp | grep -q ":5000"; then
    echo "   ✅ 포트 5000 열림 (Flask 앱)"
else
    echo "   ❌ 포트 5000 닫힘 (Flask 앱)"
fi
echo ""

# 4. 로컬 HTTP 테스트
echo "🌐 로컬 HTTP 테스트:"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost || echo "failed")
if [ "$HTTP_RESPONSE" = "200" ]; then
    echo "   ✅ HTTP 응답 정상 (200)"
elif [ "$HTTP_RESPONSE" = "failed" ]; then
    echo "   ❌ HTTP 연결 실패"
else
    echo "   ⚠️ HTTP 응답: $HTTP_RESPONSE"
fi
echo ""

# 5. 방화벽 상태 (Ubuntu UFW)
echo "🔒 방화벽 상태:"
UFW_STATUS=$(sudo ufw status | head -1)
echo "   $UFW_STATUS"
if sudo ufw status | grep -q "80/tcp"; then
    echo "   ✅ HTTP 포트 허용됨"
else
    echo "   ⚠️ HTTP 포트가 방화벽에서 허용되지 않을 수 있음"
    echo "   방화벽 규칙 추가 중..."
    sudo ufw allow 'Nginx Full'
fi
echo ""

# 6. 로그 확인
echo "📋 최근 로그:"
echo "   YouTube Score 서비스 로그:"
sudo journalctl -u youtube-score --no-pager -n 5
echo ""
echo "   Nginx 에러 로그:"
if [ -f /var/log/nginx/error.log ]; then
    sudo tail -n 3 /var/log/nginx/error.log
else
    echo "   에러 로그 없음"
fi
echo ""

# 7. 디스크 및 메모리 상태
echo "💾 시스템 리소스:"
echo "   디스크 사용량:"
df -h / | tail -1 | awk '{print "   사용됨: " $3 "/" $2 " (" $5 ")"}'
echo "   메모리 사용량:"
free -h | grep Mem | awk '{print "   사용됨: " $3 "/" $2}'
echo ""

# 8. AWS 보안 그룹 확인 힌트
echo "🔐 AWS 보안 그룹 확인 필요:"
echo "   1. EC2 Dashboard → Instances"
echo "   2. 인스턴스 선택 → Security 탭"
echo "   3. Security groups 클릭"
echo "   4. Inbound rules에 다음 규칙이 있는지 확인:"
echo "      - Type: HTTP, Port: 80, Source: 0.0.0.0/0"
echo ""

echo "🎯 접속 URL: http://$EXTERNAL_IP"
echo "================================================"
echo "문제가 계속되면 다음 명령어로 상세 로그 확인:"
echo "sudo journalctl -u youtube-score -f"