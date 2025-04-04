# Youtube Music Extractor | 유튜브 악보 추출기

> **중요: [이제 v2 및 v3을 실행하기 위해 env.py를 생성해야 합니다.](#수정-필요한-변수v2/v3)**

Python 언어 사용  
Korean comment supported. 한국어 주석 있음  
최근 주요 업데이트 04.02

***

## 추가 예정 기능

- [X] 병합 이미지를 PDF로 변환해 다운
- [X] 실행마다 영상 제목으로 폴더 생성 후 내부에 영상 파일, pdf파일, 이미지 파일 저장
- [X] 악보 이미지 구역 설정 기능 : 가로 a% to b%, 세로 x% to y%
- [X] start_time, end_time에 mm:ss식으로 작성된 시간 적용
- [X] float로 입력하는 걸 직관적으로 % 스타일로 입력
- [X] fade, push 방식으로 전환되는 악보에도 적용 (v3)
- [X] exe파일 생성해 따로 코드 편집기, python 라이브러리 설치하지 않고도 기능 사용 - Tkinter
  - [X] 터미널 결과 출력, 실행 완료 시 파일 열기 등 편의성
  - [X] env.py 자동 생성하여 gui 내에서 입력 받는 로직
  - [ ] ffmpeg 파일 내장
  - [ ] start/end percent 입력 도움(해당픽셀/전체 해상도)
  

## 실행 예시

> **런타임: 1~2분, 실행 중에는 디버그 출력문이 나옴**

> **정상 실행 완료 시 "All Done!" 출력되면 생성된 파일을 확인하면 됨.**
![image](https://github.com/user-attachments/assets/ccbcd56e-1616-43c4-b373-f48b0e5761dc)
![image](https://github.com/user-attachments/assets/cb569801-53f4-4cf8-8460-29bd80139e98)


코드 파일 경로에 url 영상파일, 병합된 악보 PDF파일 저장됨  
temp_images 파일은 임시 저장용 폴더이므로, 사용하지 않으면 됩니다.  

***

### 설치 프로그램 및 라이브러리:  

**essential installation :**
* [ffmpeg](https://www.ffmpeg.org/)
* [python3](https://www.python.org/)  

**[essential library :](./requirements.txt)**
* numpy
* opencv
* yt-dlp
* fpdf

### 수정 필요한 변수:  
> 
* url,  
* tab_region_ratio

> url변수에 유튜브 링크 넣고 하단 악보 나와있는 영역만큼 비율 변수 설정하면 됩니다  
> 그림판 - 선택 영역 도구 또는 마우스 커서 통해 픽셀 측정 가능 -> tab region ratio 또는 start/end percent 지정에 활용하시면 편합니다.

## 버전 별 구분
#### 유튜브 영상 타입에 따라 v1와 v2 파일 중 하나를 사용함
**v1**: 영상 시작부터 끝까지 악보가 나옴, 악보가 움직이지 않고 정적으로 표시됨, 추출할 악보가 영상 하단부에만 위치함  
->쉽게 영상으로부터 추출 가능, 디테일한 적용 불가  
*ex:[guitar cover with tabs&chords](https://www.youtube.com/channel/UCeWHmkuMBM760nryL8wLfLg)*  

**v2**: 영상 인트로 또는 아웃트로가 존재함, 악보가 움직이지 않고 정적으로 표시됨, 추출할 악보 구역 지정 가능  
->더 자세한 지정 가능하며 많은 영상에 적용 가능, 수정할 변수가 많음  
*ex:[하루한곡](https://www.youtube.com/channel/UCKqym7WZq6J6BDJqapiinxw) 등 여러 유튜브 영상 지정 가능*

**v3**: 영상 인트로 또는 아웃트로가 존재함, 악보가 넘어갈때마다 fade 또는 push 방식으로 움직임 , 추출할 악보 구역 지정 가능  
->더 자세한 지정 가능하며 많은 영상에 적용 가능, 수정할 변수가 많음  
*ex:[Mr.tabs](https://youtu.be/x_NGsTIJptw?si=wKx17EWYK5Fol0Nr) 등 대부분의 유튜브 영상 악보 추출 가능*
