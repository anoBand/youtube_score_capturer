import cv2
import numpy as np
import yt_dlp
from fpdf import FPDF
import os
import re

url = "youryoutubevideourl.com"

# 유튜브 메타정보를 먼저 추출하여 제목을 얻는 함수
def get_video_title(url):
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "outtmpl": "%(title)s.%(ext)s"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Untitled')
    # 파일명으로 사용하기 위해 특수문자 제거/치환
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
    return safe_title

# 유튜브 동영상 다운로드 함수
def download_youtube_video(url, folder_path):
    output_path = os.path.join(folder_path, "video.mp4")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": output_path,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# 1) 동영상 제목을 폴더명으로 만들고 폴더 생성
video_title = get_video_title(url)
folder_path = video_title

if not os.path.exists(folder_path):
    os.makedirs(folder_path, exist_ok=True)

# 2) 폴더 내부에 동영상 다운로드
video_path = download_youtube_video(url, folder_path)

# 3) 임시 이미지 저장 폴더도 해당 폴더 내부에 생성
temp_folder = os.path.join(folder_path, "temp_images")
os.makedirs(temp_folder, exist_ok=True)

cap = cv2.VideoCapture(video_path)
threshold_diff = 15  # 프레임 차이 비교 임계값
tab_region_ratio = 0.45  # 하단 몇 %를 추출할지 설정 (기본값: 45%)

prev_frame = None  # 이전 프레임 저장 변수
frame_list = []

if not cap.isOpened():
    print("Error: Could not open video file.")

while cap.isOpened():
    frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    success, frame = cap.read()

    if not success:
        break

    height, width = frame.shape[:2]
    # 설정된 비율만큼 하단 부분만 추출
    cropped_frame = frame[int(height * (1 - tab_region_ratio)):, :]
    gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)  # 흑백 변환

    if prev_frame is not None:
        diff = cv2.absdiff(prev_frame, gray_frame)
        mean_diff = np.mean(diff)

        if mean_diff < threshold_diff:
            continue

    frame_list.append(cropped_frame)
    prev_frame = gray_frame

cap.release()

def extract_tab_region(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi = gray[:, :]  # 이미 하단 부분을 받았으므로 전체 영역 사용

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # 가장 큰 컨투어 선택
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        x, y, w, h = cv2.boundingRect(contours[0])
        return frame[y:y + h, x:x + w]

    return None

tab_images = []
for frame in frame_list:
    tab_region = extract_tab_region(frame)
    if tab_region is not None:
        tab_images.append(tab_region)

if tab_images:
    print(f"Total TAB regions found: {len(tab_images)}")
else:
    print("No valid TAB regions were detected in any frame.")

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
        # A4 폭 기준으로 높이 비율을 계산
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
