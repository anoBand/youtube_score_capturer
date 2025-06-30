from typing import Optional, List

URL: str = "https://youtu.be/3ls1r_fPJKU?si=aJr1RZB5xKXngkMz"

# 동영상 분석 구간 (초 단위)
START_TIME_RAW: Optional[str] = '13' # 정수 입력 시 초로 인식 (기본 처음부터)
END_TIME_RAW: Optional[str] = '100'     # mm:ss 형식 입력 가능, None 입력 시 끝까지

# 프레임 비교 임계값(중복 제거)
THRESHOLD_DIFF: float = 5.0

# 잘라낼 영역 퍼센트(0% ~ 100%)
X_START_PERCENT_RAW: float = 0.0
X_END_PERCENT_RAW: float   = 60.0
Y_START_PERCENT_RAW: float = 70.0
Y_END_PERCENT_RAW: float   = 100.0

# 전환 안정화 시간 (초)
TRANSITION_STABLE_SEC: float = 2.0

# 출력 폴더명 접두어
BASE_FOLDER_NAME: str = "music_file_"

# v3에서 사용하지 않는 변수들 (호환성 유지용)
TAB_REGION_RATIO: float = 0.45  # v1 전용, v3에서는 사용 안함
