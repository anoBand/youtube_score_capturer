
# 🎼 YouTube 악보 PDF 추출기

유튜브 영상 속에 표시된 악보를 자동으로 인식하여 PDF로 추출해주는 간단한 프로그램입니다. 복잡한 과정 없이 몇 번의 클릭으로 간편하게 악보를 얻을 수 있습니다.

---

## 🚩 주요 기능

- **유튜브 영상에서 악보 자동 추출** 및 **PDF로 저장**
- 다양한 **악보 전환 방식(버전)** 제공
  - 버전이 높을수록 더 세부적이며 다양한 변수를 조정할 수 있습니다.
- **쉬운 설치** 및 **간단한 실행** 방법 제공

---

## 📥 설치 방법

### 1. Python 설치
아래 링크에서 Python 최신 버전을 설치해주세요:

[👉 Python 설치하러 가기](https://www.python.org/downloads/)

설치할 때 "Add Python to PATH" 옵션을 꼭 체크해주세요!

### 2. 프로그램 다운로드

압축 파일을 다운로드한 후 원하는 위치에 압축을 풀어주세요.

[👉 Google Drive에서 다운로드하기](https://drive.google.com/file/d/1dj0XC9n5LOTS9t5GnV7UO-O9S-msMaFM/view?usp=sharing)

---

## 🚀 사용 방법

1. 폴더에서 `gui.exe`를 더블클릭하여 실행합니다.
2. 프로그램이 열리면, 유튜브 영상 링크를 입력하고, 원하는 악보 추출 방식을 선택하세요.
   - **버전 1:** 기본적인 악보 추출 (가장 빠름)
   - **버전 2:** 중간 수준의 디테일
   - **버전 3 이상:** 상세하고 다양한 옵션 제공
3. 영상의 URL과 버전 별 요구 항목을 입력 후 저장하세요.
4. 실행 후, 자동으로 악보 PDF가 생성됩니다.

**지원 환경:** Windows

---

## ⏱️ 실행 시간

- 악보 추출까지 대략 **2분 정도**가 소요됩니다.

---

## 📌 주의사항
- 인터넷 연결이 필요합니다.
- 영상 길이에 따라 소요 시간이 약간 달라질 수 있습니다.

---

**이제 간편하게 유튜브에서 원하는 악보를 추출해 보세요! 🎸🎹🎶**


***
 ## 추가 예정 기능

- [X] 병합 이미지를 PDF로 변환해 다운
- [X] 실행마다 영상 제목으로 폴더 생성 후 내부에 영상 파일, pdf파일, 이미지 파일 저장
- [X] 악보 이미지 구역 설정 기능 : 가로 a% to b%, 세로 x% to y% (v2)
- [X] start_time, end_time에 mm:ss식으로 작성된 시간 적용
- [X] float로 입력하는 걸 직관적으로 % 스타일로 입력
- [X] fade, push 방식으로 전환되는 악보에도 적용 (v3)
- [X] exe파일 생성해 따로 코드 편집기, python 라이브러리 설치하지 않고도 기능 사용
  - [X] 터미널 결과 출력, 실행 완료 시 파일 열기 등 편의성
  - [X] env.py 자동 생성하여 gui 내에서 입력 받는 로직
  - [X] ffmpeg 파일 내장
  - [X] start/end percent 입력 도움(해당픽셀/전체 해상도)
  - [X] src 폴더로 파일 정리하여 사용자 경험에 도움
- [ ] 코드 최적화, UI 업데이트 (점진적)  

---

## 버전 별 구분
#### 유튜브 영상 타입에 따라 v1와 v2, v3 파일 중 하나를 사용함
 **v1**: 영상 시작부터 끝까지 악보가 나옴, 악보가 움직이지 않고 정적으로 표시됨, **추출할 악보가 영상 하단부에만 위치함**  
->쉽게 영상으로부터 추출 가능, 디테일한 적용 불가  
*ex:[guitar cover with tabs&chords](https://www.youtube.com/channel/UCeWHmkuMBM760nryL8wLfLg)*  
> ![31](https://github.com/user-attachments/assets/1a92af92-7eab-4df2-ba92-0b5fa8ed8384)

**v2**: 영상 인트로 또는 아웃트로가 존재함, 악보가 움직이지 않고 정적으로 표시됨, **추출할 악보 구역 지정 가능**  
->더 자세한 지정 가능하며 많은 영상에 적용 가능, 수정할 변수가 많음  
*ex:[하루한곡](https://www.youtube.com/channel/UCKqym7WZq6J6BDJqapiinxw) 등 여러 유튜브 영상 지정 가능*
> ![32](https://github.com/user-attachments/assets/2684f5ff-cd06-4904-9f5b-9c7317a6936e)



 **v3**: 영상 인트로 또는 아웃트로가 존재함, **악보가 넘어갈때마다 fade 또는 push 방식으로 움직임** , 추출할 악보 구역 지정 가능  
->더 자세한 지정 가능하며 많은 영상에 적용 가능, 수정할 변수가 많음  
*ex:[Mr.tabs](https://youtu.be/x_NGsTIJptw?si=wKx17EWYK5Fol0Nr) 등 대부분의 유튜브 영상 악보 추출 가능*
> ![33](https://github.com/user-attachments/assets/36f2f306-b7fa-4f61-b72d-2af8630ec3c9)

---


## 실행 예시
> ![image](https://github.com/user-attachments/assets/93f570df-3011-4ecb-992c-4367193782ba)  


https://github.com/user-attachments/assets/0d543e94-0aea-49ac-9fae-18fc0d717135



* 추출 영역(%) 지정 시 그림판 좌하단의 커서 px 모니터링 활용 시 편리함  
* 파일 경로에 url 영상파일, 병합된 악보 PDF파일 저장됨  
* temp_images 파일은 임시 저장용 폴더이므로, 사용하지 않으면 됩니다.  
