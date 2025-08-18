############################################
# 1) import 구문
############################################
# 내장 라이브러리
import os
import re
import argparse
from typing import Optional, List
# 외장 라이브러리
import cv2
import yt_dlp
import numpy as np
from fpdf import FPDF
import sys

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
        # ffmpeg 없이 다운로드하기 위해, 이미 합쳐진 mp4 포맷 중 가장 좋은 것을 선택합니다.
        "format": "best[ext=mp4]/best",
        "outtmpl": output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("Downloading video from YouTube... (yt_dlp)")
        ydl.download([url])
    print("Download complete:", output_path)
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
def main():
    parser = argparse.ArgumentParser(description="YouTube 영상에서 악보 이미지를 추출하여 PDF로 저장합니다.")
    parser.add_argument("--url", required=True, help="YouTube 영상 URL")
    parser.add_argument("--start-time", default='0', help="분석 시작 시간 (초 또는 mm:ss)")
    parser.add_argument("--end-time", default=None, help="분석 종료 시간 (초 또는 mm:ss)")
    parser.add_argument("--threshold", type=float, default=5.0, help="프레임 비교 임계값")
    parser.add_argument("--x-start", type=float, default=0.0, help="잘라낼 X 시작 퍼센트")
    parser.add_argument("--x-end", type=float, default=100.0, help="잘라낼 X 끝 퍼센트")
    parser.add_argument("--y-start", type=float, default=0.0, help="잘라낼 Y 시작 퍼센트")
    parser.add_argument("--y-end", type=float, default=100.0, help="잘라낼 Y 끝 퍼센트")
    parser.add_argument("--transition-sec", type=float, default=2.0, help="전환 안정화 시간(초)")
    parser.add_argument("--base-folder", default="music_file_", help="출력 폴더명 접두어")
    args = parser.parse_args()

    # 3-1) 초기변수
    is_in_transition = False
    stable_time = 0.0
    last_pos_sec = 0.0

    # 3-2) 입력값 변환
    START_TIME = parse_time(args.start_time)
    END_TIME   = parse_time(args.end_time)

    X_START_PERCENT: float = args.x_start / 100
    X_END_PERCENT:   float = args.x_end   / 100
    Y_START_PERCENT: float = args.y_start / 100
    Y_END_PERCENT:   float = args.y_end   / 100

    ############################################
    # 4) 결과 저장할 폴더 생성 (상위 폴더에 생성)
    ############################################
    base_dir = os.getcwd()
    parent_dir = os.path.dirname(base_dir)

    counter = 1
    while True:
        folder_path = os.path.join(parent_dir, f"{args.base_folder}{counter}")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            break
        counter += 1
    print(f"'{folder_path}' 디렉토리가 준비되었습니다.")
    
    video_path: str = download_youtube_video(args.url, folder_path)

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
    print(f"Video duration: {video_duration:.2f} sec, FPS: {fps:.2f}")

    modified_end_time: float = END_TIME if (END_TIME and END_TIME < video_duration) else video_duration
    print(f"Analyzing frames from {START_TIME or 0:.2f}s to {modified_end_time:.2f}s")

    if START_TIME and START_TIME > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, START_TIME * 1000)

    prev_frame: Optional[np.ndarray] = None
    frame_list: List[np.ndarray] = []

    ############################################
    # 8) 프레임 추출 (START_TIME ~ modified_end_time)
    ############################################
    frame_count: int = 0
    PRINT_INTERVAL = 90

    while True:
        current_pos_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if current_pos_sec > modified_end_time:
            break

        success, frame = cap.read()
        if not success:
            break

        dt = current_pos_sec - last_pos_sec
        last_pos_sec = current_pos_sec
        frame_count += 1

        if frame_count % PRINT_INTERVAL == 0:
            print(f"[Frame Extraction] Processed {frame_count} frames... (stable_time={stable_time:.2f}, in_transition={is_in_transition})")

        height, width = frame.shape[:2]

        x_start: int = int(width  * X_START_PERCENT)
        x_end:   int = int(width  * X_END_PERCENT)
        y_start: int = int(height * Y_START_PERCENT)
        y_end:   int = int(height * Y_END_PERCENT)

        cropped_frame: np.ndarray = frame[y_start:y_end, x_start:x_end]
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray_frame)
            mean_diff = float(np.mean(diff))

            if mean_diff > args.threshold:
                is_in_transition = True
                stable_time = 0.0
            else:
                if is_in_transition:
                    stable_time += dt
                    if stable_time >= args.transition_sec:
                        frame_list.append(cropped_frame)
                        is_in_transition = False
        else:
            frame_list.append(cropped_frame)

        prev_frame = gray_frame

    cap.release()

    print(f"Frame loop finished. Total frames read: {frame_count}, final collected frames: {len(frame_list)}")

    tab_images: List[np.ndarray] = []
    for f in frame_list:
        tab_region: Optional[np.ndarray] = extract_tab_region(f)
        if tab_region is not None:
            tab_images.append(tab_region)

    print(f"Total TAB regions found: {len(tab_images)}")

    pdf_output_path: str = os.path.join(folder_path, "output.pdf")
    save_images_to_pdf(tab_images, pdf_output_path, temp_folder)

    print("All done!")

if __name__ == "__main__":
    main()