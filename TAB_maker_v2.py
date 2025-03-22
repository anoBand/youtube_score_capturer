
import cv2
import numpy as np
import yt_dlp
from fpdf import FPDF
import os
import re

############################################
# 1) 사용자 지정 변수 (초기화)
############################################
url = "youryoutubeurl.com"

# 동영상 분석 구간 (초 단위)
start_time = 0      # 0초부터 (기본값)
end_time   = None    # None이면 영상 끝까지 (예: 30.0 등으로 지정 가능)

# 프레임 비교 임계값(중복 제거)
threshold_diff = 5

# 잘라낼 영역 퍼센트(0.0 ~ 1.0 사이)
# 기본값: 전체 화면(0.0~1.0)
x_start_percent = 0.0
x_end_percent   = 1.0
y_start_percent = 0.0
y_end_percent   = 1.0
############################################

############################################
# 2) 폴더 이름을 자동 증가 방식으로 생성
############################################
base_folder_name = "music_file_"  # 기본 접두사
counter = 1
while True:
    folder_path = f"{base_folder_name}{counter}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        break
    counter += 1

print(f"Folder created (or found) at: {folder_path}")

############################################
# 3) 유튜브 영상 다운로드 (video.mp4)
############################################
def download_youtube_video(url, folder_path):
    """유튜브 영상을 지정 폴더에 다운로드 후, 저장된 파일 경로 반환"""
    output_path = os.path.join(folder_path, "video.mp4")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": output_path,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

video_path = download_youtube_video(url, folder_path)

############################################
# 4) 임시 이미지 저장 폴더 생성
############################################
temp_folder = os.path.join(folder_path, "temp_images")
os.makedirs(temp_folder, exist_ok=True)

############################################
# 5) 동영상 열기
############################################
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
video_duration = total_frames / fps if fps else 0

# end_time이 None이면 영상 끝까지
if end_time is None or end_time > video_duration:
    end_time = video_duration

# start_time 위치로 이동 (밀리초 기준)
if start_time > 0:
    cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

prev_frame = None
frame_list = []

########################################
# 6) 프레임 추출 (start_time ~ end_time)
########################################
while True:
    current_pos_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
    if current_pos_sec > end_time:
        break

    success, frame = cap.read()
    if not success:
        break

    height, width = frame.shape[:2]

    x_start = int(width  * x_start_percent)
    x_end   = int(width  * x_end_percent)
    y_start = int(height * y_start_percent)
    y_end   = int(height * y_end_percent)

    cropped_frame = frame[y_start:y_end, x_start:x_end]
    gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

    # 중복 제거 (프레임 차이)
    if prev_frame is not None:
        diff = cv2.absdiff(prev_frame, gray_frame)
        mean_diff = np.mean(diff)
        if mean_diff < threshold_diff:
            continue

    frame_list.append(cropped_frame)
    prev_frame = gray_frame

cap.release()

########################################
# 7) 탭 영역(가장 큰 컨투어) 추출
########################################
def extract_tab_region(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi = gray[:, :]

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        x, y, w, h = cv2.boundingRect(contours[0])
        return frame[y:y + h, x:x + w]
    return None

tab_images = []
for f in frame_list:
    tab_region = extract_tab_region(f)
    if tab_region is not None:
        tab_images.append(tab_region)

if tab_images:
    print(f"Total TAB regions found: {len(tab_images)}")
else:
    print("No valid TAB regions were detected in any frame.")

########################################
# 8) 이미지 병합 (세로 방향)
########################################
def merge_images(images):
    images = [img for img in images if img is not None and img.size > 0]
    if not images:
        print("Error: No valid images to merge.")
        return None

    max_width = max(img.shape[1] for img in images)
    total_height = sum(img.shape[0] for img in images)
    merged_image = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255

    y_offset = 0
    for img in images:
        h, w, _ = img.shape
        merged_image[y_offset:y_offset + h, :w] = img
        y_offset += h

    return merged_image

final_image = merge_images(tab_images)
merged_image_path = os.path.join(folder_path, "merged_tabs.png")

if final_image is not None:
    cv2.imwrite(merged_image_path, final_image)
    print("Merged image saved successfully.")
else:
    print("No valid image to save.")

########################################
# 9) PDF로 저장
########################################
def save_images_to_pdf(images, pdf_filename):
    print(f"Debug: Total images for PDF = {len(images)}")
    if len(images) > 0:
        print(f"Debug: First image shape = {images[0].shape}")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=5)
    a4_width, a4_height = 210, 297  # A4 크기 (mm)

    merged_tab_images = []
    current_height = 0
    current_page_images = []

    for img in images:
        img_height = (img.shape[0] / img.shape[1]) * a4_width
        if current_height + img_height > a4_height:
            merged_tab_images.append(current_page_images)
            current_page_images = []
            current_height = 0

        current_page_images.append(img)
        current_height += img_height

    if current_page_images:
        merged_tab_images.append(current_page_images)

    for page_index, page_images in enumerate(merged_tab_images):
        print(f"Debug: Page {page_index + 1}, Number of images = {len(page_images)}")
        pdf.add_page()
        y_offset = 10
        for i, img in enumerate(page_images):
            temp_filename = os.path.join(temp_folder, f"temp_img_{page_index + 1}_{i + 1}.png")
            cv2.imwrite(temp_filename, img)
            pdf.image(temp_filename, x=10, y=y_offset, w=a4_width - 20)
            y_offset += (img.shape[0] / img.shape[1]) * (a4_width - 20) + 5

    pdf.output(pdf_filename)
    print(f"PDF saved successfully as {pdf_filename}")

pdf_output_path = os.path.join(folder_path, "output.pdf")
save_images_to_pdf(tab_images, pdf_output_path)
