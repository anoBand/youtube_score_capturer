#!/bin/bash

LOG_FILE="/var/log/youtube-score/cleanup.log"
APP_DIR="/home/ubuntu/youtube-score-capturer"

# 로그 파일 생성 (없다면)
sudo mkdir -p /var/log/youtube-score
sudo touch $LOG_FILE
sudo chown ubuntu:ubuntu $LOG_FILE

echo "$(date): 🧹 정리 작업 시작" >> $LOG_FILE

# 1시간 이상 된 music_file 폴더들 삭제
DELETED_COUNT=$(find $APP_DIR -name "music_file_*" -type d -mtime +0.04 2>/dev/null | wc -l)
find $APP_DIR -name "music_file_*" -type d -mtime +0.04 -exec rm -rf {} + 2>/dev/null
if [ $DELETED_COUNT -gt 0 ]; then
    echo "$(date): 🗑️ $DELETED_COUNT 개의 오래된 폴더 삭제됨" >> $LOG_FILE
fi

# /tmp의 오래된 파일들 정리
find /tmp -name "*.mp4" -o -name "*.webm" -o -name "*.png" -mtime +1 -delete 2>/dev/null

# 디스크 사용량 체크 (90% 이상이면 경고)
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "$(date): ⚠️ 디스크 사용량이 ${DISK_USAGE}%입니다!" >> $LOG_FILE
elif [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): 📊 디스크 사용량: ${DISK_USAGE}%" >> $LOG_FILE
fi

echo "$(date): ✅ 정리 작업 완료" >> $LOG_FILE
