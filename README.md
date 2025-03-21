# yt-tab-img-extractor

Python 언어 사용

Korean comment supported. 한국어 주석 있음

최근 주요 업데이트 03.19
***
## 추가 예정 기능

#### ~~병합 이미지를 PDF로 변환해 다운~~(완료)

#### ~~실행마다 영상 제목으로 폴더 생성 후 내부에 영상 파일, pdf파일, 이미지 파일 저장~~(완료)

#### 악보 이미지 구역 설정 기능 : 가로 a% to b%, 세로 x% to y% (개별파일 사용 예정) 

#### fade식으로 전환되는 악보에도 적용 (개별파일 사용 예정) 

#### 일정 속도로 움직이는 악보 형식에 대해 추출

#### 다른 악기의 악보 형식에도 적용

#### 웹 UI로 구현해 따로 코드 파일 실행하지 않고도 기능 사용

## 실행 예시

#### 영상 길이, PC성능에 따라 런타임 다를 수 있으나 1~2분정도 걸립니다.
#### 정상 실행 완료 시 "PDF saved successfully as output.pdf" 출력되니 확인하시면 됩니다.
![image](https://github.com/user-attachments/assets/d35b6e3d-86f1-42da-a213-bf53639e8cd3)


코드 파일 경로에 url 영상파일, 병합된 악보 이미지파일, 병합된 악보 PDF파일 저장됨  
이미지는 Chrome 탭으로 열고 확대해서 보기를 추천합니다.
***
### 설치 프로그램 및 라이브러리:  

**essential installation :**
ffmpeg,
python  
**essential library :**
numpy,
opencv,
yt-dlp
fpdf

### 수정 필요한 변수:  
url,
tab_region_ratio (필요시)

***

url변수에 유튜브 링크 넣고 하단 악보 나와있는 영역만큼 비율 변수 설정하면 됩니다!  
라이브러리, 프로그램 설치 방법은 구글링 하시고 질문주세요
