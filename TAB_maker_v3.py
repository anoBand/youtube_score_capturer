############################################
# 1) import 구문
############################################
# 내장 라이브러리
import os
import re
from typing import Optional, List
# 외장 라이브러리
import cv2
import yt_dlp
import numpy as np
from fpdf import FPDF

# env.py 파일에서 상수 불러오기
from env import (
    URL, START_TIME_RAW, END_TIME_RAW,
    THRESHOLD_DIFF,
    X_START_PERCENT_RAW, X_END_PERCENT_RAW,
    Y_START_PERCENT_RAW, Y_END_PERCENT_RAW,
    TRANSITION_STABLE_SEC,
    BASE_FOLDER_NAME
)

############################################
# 2) 함수 선언
############################################

def parse_time(value: Optional[str]) -> Optional[float]:
    """
    None -> None
    정수/실수 형태 -> float(초)
    'mm:ss' 형태 -> (mm * 60 + ss)
    공백/잘못된 형태 -> ValueError
    """
    if value is None:
        return None
    
    value = value.strip()
    if not value:
        return None

    # 'mm:ss' 형태인지 확인
    if ':' in value:
        parts = value.split(':')
        if len(parts) == 2:
            mm_str, ss_str = parts
            mm = float(mm_str)
            ss = float(ss_str)
            return mm * 60 + ss
        else:
            raise ValueError(f"Invalid time format: {value}")
    
    # ':'가 없으면 정수/실수로 인식
    return float(value)

def download_youtube_video(url: str, folder_path: str) -> str:
    """
    유튜브 영상을 지정 폴더에 다운로드 후, 저장된 파일 경로를 반환한다.
    """
    output_path: str = os.path.join(folder_path, "video.mp4")
    ydl_opts: dict = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4"
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

def extract_tab_region(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    프레임에서 가장 큰 컨투어 영역(가령 악보 TAB)을 찾아 잘라낸다.
    컨투어가 없으면 None을 반환한다.
    """
    gray: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi: np.ndarray = gray[:, :]

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        x, y, w, h = cv2.boundingRect(contours[0])
        return frame[y:y + h, x:x + w]
    return None

def save_images_to_pdf(images: List[np.ndarray], pdf_filename: str, temp_folder: str) -> None:
    """
    이미지 리스트를 PDF로 저장한다.
    한 페이지에 여러 이미지를 순차적으로 배치한다.
    """
    print(f"Debug: Total images for PDF = {len(images)}")
    if images:
        print(f"Debug: First image shape = {images[0].shape}")

    pdf: FPDF = FPDF()
    pdf.set_auto_page_break(auto=True, margin=5)

    # A4 크기(mm)
    a4_width: float = 210
    a4_height: float = 297  

    # 페이지 단위로 이미지를 모아두는 변수들
    merged_tab_images: List[List[np.ndarray]] = []
    current_height: float = 0
    current_page_images: List[np.ndarray] = []

    for img in images:
        img_height: float = (img.shape[0] / img.shape[1]) * a4_width
        if current_height + img_height > a4_height:
            merged_tab_images.append(current_page_images)
            current_page_images = []
            current_height = 0
        current_page_images.append(img)
        current_height += img_height

    if current_page_images:
        merged_tab_images.append(current_page_images)

    # 페이지별로 PDF에 삽입
    for page_index, page_images in enumerate(merged_tab_images):
        print(f"Debug: Page {page_index + 1}, Number of images = {len(page_images)}")
        pdf.add_page()
        y_offset: float = 10
        for i, img in enumerate(page_images):
            temp_filename: str = os.path.join(temp_folder, f"temp_img_{page_index + 1}_{i + 1}.png")
            cv2.imwrite(temp_filename, img)
            pdf.image(temp_filename, x=10, y=y_offset, w=a4_width - 20)
            y_offset += (img.shape[0] / img.shape[1]) * (a4_width - 20) + 5

    pdf.output(pdf_filename)
    print(f"PDF saved successfully as {pdf_filename}")

############################################
# 3) 메인 코드
############################################

# 3-1) 초기변수
is_in_transition = False
stable_time = 0.0
last_pos_sec = 0.0

# 3-2) 입력값 변환
START_TIME = parse_time(START_TIME_RAW)
END_TIME   = parse_time(END_TIME_RAW)

# 퍼센트도 "정수" 입력받았으므로 100으로 나눠서 0.x 형태로
X_START_PERCENT: float = X_START_PERCENT_RAW / 100
X_END_PERCENT:   float = X_END_PERCENT_RAW   / 100
Y_START_PERCENT: float = Y_START_PERCENT_RAW / 100
Y_END_PERCENT:   float = Y_END_PERCENT_RAW   / 100

if __name__ == "__main__":
    ############################################
    # 4) 결과 저장할 폴더 생성
    ############################################
    counter: int = 1
    while True:
        folder_path: str = f"{BASE_FOLDER_NAME}{counter}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            break
        counter += 1
    print(f"'{folder_path}' 디렉토리가 준비되었습니다.")

    # 5) 유튜브 영상 다운로드
    video_path: str = download_youtube_video(URL, folder_path)

    # 6) 임시 이미지 저장 폴더 생성
    temp_folder: str = os.path.join(folder_path, "temp_images")
    os.makedirs(temp_folder, exist_ok=True)

    ############################################
    # 7) 비디오 정보 가져오기
    ############################################
    cap: cv2.VideoCapture = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("에러: 비디오 파일을 열 수 없습니다.")
        exit(1)

    fps: float = cap.get(cv2.CAP_PROP_FPS)
    total_frames: float = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration: float = total_frames / fps if fps else 0.0

    # END_TIME이 None이거나 영상 길이를 넘어가면 영상 끝까지
    modified_end_time: float = END_TIME if (END_TIME and END_TIME < video_duration) else video_duration

    # START_TIME 위치로 이동 (밀리초 기준)
    if START_TIME and START_TIME > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, START_TIME * 1000)

    prev_frame: Optional[np.ndarray] = None
    frame_list: List[np.ndarray] = []

    ############################################
    # 8) 프레임 추출 (START_TIME ~ modified_end_time)
    ############################################
    while True:
        current_pos_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if current_pos_sec > modified_end_time:
            break

        success, frame = cap.read()
        if not success:
            break

        # dt(현재 프레임 ~ 이전 프레임 시간차) 계산
        dt = current_pos_sec - last_pos_sec
        last_pos_sec = current_pos_sec
        height, width = frame.shape[:2]

        # 사용자 지정 영역(percent)만큼 크롭
        x_start: int = int(width  * X_START_PERCENT)
        x_end:   int = int(width  * X_END_PERCENT)
        y_start: int = int(height * Y_START_PERCENT)
        y_end:   int = int(height * Y_END_PERCENT)

        cropped_frame: np.ndarray = frame[y_start:y_end, x_start:x_end]
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray_frame)
            mean_diff = float(np.mean(diff))

            # [1] 화면이 많이 변하면(전환 중) => stable_time 초기화
            #     'is_in_transition' 상태가 True
            if mean_diff > THRESHOLD_DIFF:
                is_in_transition = True
                stable_time = 0.0

            else:
                # [2] 변화가 작으면 => 안정화 구간 누적
                if is_in_transition:
                    stable_time += dt
                    # 2초 이상 안정이면 "전환 완료"로 판단
                    if stable_time >= TRANSITION_STABLE_SEC:
                        # -> 이 시점 프레임을 채택
                        frame_list.append(cropped_frame)
                        is_in_transition = False
                else:
                    # 이미 안정 상태라면 별도 처리 X
                    pass

        else:
            # 첫 프레임은 일단 저장하거나, 또는 무시
            # 여기서는 "첫 악보"라 보고 한번 추가해도 됨
            frame_list.append(cropped_frame)

        prev_frame = gray_frame

    cap.release()


    # 9) TAB(악보) 영역 추출
    tab_images: List[np.ndarray] = []
    for f in frame_list:
        tab_region: Optional[np.ndarray] = extract_tab_region(f)
        if tab_region is not None:
            tab_images.append(tab_region)


    # 10) PDF로 저장
    pdf_output_path: str = os.path.join(folder_path, "output.pdf")
    save_images_to_pdf(tab_images, pdf_output_path, temp_folder)
