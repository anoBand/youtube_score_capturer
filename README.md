# YouTube Score Capturer

## 소개
YouTube 영상에서 악보를 자동으로 캡처하여 PDF로 만들어주는 도구임

## 주요 기능
- **영상 처리**: yt-dlp로 YouTube 영상을 다운로드하거나 스트리밍하여 분석함
- **프레임 캡처**: OpenCV를 이용해 설정된 구간, 좌표의 악보 영역만 정밀하게 캡처함
- **중복 방지**: 이전 프레임과 비교하여 변화가 있는 경우에만 저장하여 중복을 최소화함
- **PDF 변환**: 캡처된 이미지들을 A4 크기에 맞춰 자동으로 배치하고 하나의 PDF 파일로 생성함
- **웹 UI 제공**: Flask 기반 웹 인터페이스를 통해 직관적인 조작과 실시간 미리보기를 지원함

## 설치 및 실행 (웹 배포 리팩터링 중)
1. 필요 라이브러리 설치: `pip install -r requirements.txt`
2. 애플리케이션 실행: `python app.py`
3. 웹 브라우저 접속: `http://localhost:5000`

## 기술 스택
- **Language**: Python
- **Web**: Flask
- **Media**: OpenCV, yt-dlp, Pillow, FPDF
