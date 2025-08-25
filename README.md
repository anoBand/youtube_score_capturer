# YouTube Score Capturer

YouTube 동영상에서 악보를 추출하여 PDF로 변환하는 웹 애플리케이션입니다.

## 🚀 배포 방법

### Oracle Cloud 인스턴스에서 실행

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/youtube-score-capturer.git
cd youtube-score-capturer

# 2. 배포 스크립트 실행
./scripts/deploy.sh

# 3. 브라우저에서 접속
# http://your-oracle-ip
```

### 업데이트

```bash
# 최신 버전으로 업데이트
./scripts/update.sh
```

### 관리 명령어

```bash
# 서비스 상태 확인
sudo systemctl status youtube-score

# 로그 확인
sudo journalctl -u youtube-score -f

# 정리 작업 수동 실행
./scripts/cleanup.sh

# 모니터링 수동 실행
./scripts/monitor.sh
```

## 📋 시스템 요구사항

- Ubuntu 20.04+
- Python 3.8+
- ffmpeg
- 최소 1GB RAM
- 최소 10GB 디스크 공간

## ⚠️ 주의사항

이 애플리케이션은 개인적 용도로만 사용하시기 바랍니다.
YouTube의 이용약관을 준수해주세요.
