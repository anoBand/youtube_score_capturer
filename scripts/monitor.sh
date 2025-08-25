#!/bin/bash

SERVICE_NAME="youtube-score"
LOG_FILE="/var/log/youtube-score/monitor.log"

# 로그 파일 생성 (없다면)
sudo mkdir -p /var/log/youtube-score
sudo touch $LOG_FILE
sudo chown ubuntu:ubuntu $LOG_FILE

# 서비스 상태 확인
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): ❌ $SERVICE_NAME 서비스가 중단됨. 재시작 중..." >> $LOG_FILE
    sudo systemctl restart $SERVICE_NAME
    sleep 5
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): ✅ $SERVICE_NAME 서비스 재시작 성공" >> $LOG_FILE
    else
        echo "$(date): 🚨 $SERVICE_NAME 서비스 재시작 실패!" >> $LOG_FILE
    fi
fi

# HTTP 응답 확인
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 http://localhost/ || echo "000")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "$(date): ⚠️ HTTP 응답 오류: $HTTP_STATUS" >> $LOG_FILE
fi
