# Youtube Music Extractor | 유튜브 악보 추출기

> **중요: [이제 v2를 실행하기 위해 env.py를 생성해야 합니다.](#수정-필요한-변수v2)**

Python 언어 사용  
Korean comment supported. 한국어 주석 있음  
최근 주요 업데이트 03.31

***

## 추가 예정 기능

- [X] 병합 이미지를 PDF로 변환해 다운
- [X] 실행마다 영상 제목으로 폴더 생성 후 내부에 영상 파일, pdf파일, 이미지 파일 저장
- [X] 악보 이미지 구역 설정 기능 : 가로 a% to b%, 세로 x% to y%
- [X] start_time, end_time에 mm:ss식으로 작성된 시간 적용
- [X] float로 입력하는 걸 직관적으로 % 스타일로 입력
- [ ] fade, push 방식으로 전환되는 악보에도 적용 (v3 예정)
- [ ] exe파일 생성하는 GUI 프로그램 이용해 따로 코드 파일 실행하지 않고도 기능 사용
  - [ ] start/end percent 입력 도움(해당픽셀/전체 해상도)
  - [ ] 터미널 결과 출력, 실행 완료 시 파일 열기 등 편의성

## 실행 예시

> **런타임: 1~2분, 최적화 예정**

> **정상 실행 완료 시 "PDF saved successfully as music_file_(번호)\output.pdf" 출력되니 확인하시면 됩니다.**
![image](https://github.com/user-attachments/assets/ccbcd56e-1616-43c4-b373-f48b0e5761dc)
![image](https://github.com/user-attachments/assets/897fac09-e3fd-4334-8ced-810092198fd0)


코드 파일 경로에 url 영상파일, 병합된 악보 이미지파일, 병합된 악보 PDF파일 저장됨  
이미지는 Chrome 탭으로 열고 확대해서 보기를 추천합니다.

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

### 수정 필요한 변수(v1):  
* url,  
* tab_region_ratio (선택적)

### 수정 필요한 변수(v2):  
**중요: v2부터는 아래와 같은 env.py 파일을 직접 만들어주어야 합니다.**
```python
from typing import Optional, List
URL: str = "https://youtu.be/6JLXenv6yGU?si=2ftfs7IjqO6_Nddo"

# 동영상 분석 구간 (초 단위)
START_TIME_RAW: Optional[str] = "0" #정수 입력 시 초로 인식 (기본 처음부터)
END_TIME_RAW:   Optional[str] = None #mm:ss 형식 입력 가능 (기본 영상 끝까지)

# 프레임 비교 임계값(중복 제거)
THRESHOLD_DIFF: float = 5

# 잘라낼 영역 퍼센트(0% ~ 100%) RAW에서 입력
# v2 파일 메인 코드에서 소수로 변환
X_START_PERCENT_RAW: float = 0
X_END_PERCENT_RAW: float   = 65
Y_START_PERCENT_RAW: float = 70
Y_END_PERCENT_RAW: float   = 97

# 출력 폴더명 접두어
BASE_FOLDER_NAME: str = "music_file_"
```
* URL  
* START_TIME, END_TIME (선택적)  
* X_START_PERCENT / X_END_PERCENT : 왼쪽부터 가로 몇 %부터 몇 %까지 사용할 것인지를 지정  
* Y_START_PERCENT / Y_END_ PERCENT : **위부터** 세로 몇 %부터 몇 %까지 사용할 것인지를 지정  

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
