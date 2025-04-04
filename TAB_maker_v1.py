import cv2
import numpy as np
import yt_dlp
from fpdf import FPDF
import os
import re

# env.py에서 필요한 상수 불러오기
from env import URL, THRESHOLD_DIFF, TAB_REGION_RATIO, BASE_FOLDER_NAME


############################################
# 1) 유튜브 다운로드 함수
############################################
def download_youtube_video(url, folder_path):
    output_path = os.path.join(folder_path, "video.mp4")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": output_path,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    }
    print("Downloading video from YouTube... (yt_dlp)")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("Download complete:", output_path)
    return output_path


############################################
# 2) 탭 컨투어 영역 추출 함수
############################################
def extract_tab_region(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi = gray[:, :]  # 이미 하단 부분을 받았으므로 전체 영역 사용

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        x, y, w, h = cv2.boundingRect(contours[0])
        return frame[y:y + h, x:x + w]

    return None


############################################
# 3) 이미지 병합 함수
############################################
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


############################################
# 4) PDF 저장 함수
############################################
def save_images_to_pdf(images, pdf_filename, temp_folder):
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
        # A4 폭 대비로 이미지 높이를 계산
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


############################################
# 5) 메인 로직
############################################
if __name__ == "__main__":

    ############################################
    # (A) 폴더 생성 (BASE_FOLDER_NAME + 숫자)
    ############################################
    counter = 1
    while True:
        folder_path = f"{BASE_FOLDER_NAME}{counter}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            break
        counter += 1

    print(f"'{folder_path}' 폴더가 준비되었습니다.")

    ############################################
    # (B) 유튜브 영상 다운로드
    ############################################
    video_path = download_youtube_video(URL, folder_path)

    ############################################
    # (C) 임시 이미지 폴더 생성
    ############################################
    temp_folder = os.path.join(folder_path, "temp_images")
    os.makedirs(temp_folder, exist_ok=True)

    ############################################
    # (D) 영상 열기
    ############################################
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        exit(1)

    prev_frame = None
    frame_list = []

    ############################################
    # (E) 프레임 추출
    ############################################
    PRINT_INTERVAL = 90  # 90프레임마다 진행 상황 출력
    frame_count = 0
    saved_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        # 90프레임마다 한 번씩 진행 상황 표시
        if frame_count % PRINT_INTERVAL == 0:
            print(f"[Frame Extraction] Processed {frame_count} frames... (kept={saved_count})")

        height, width = frame.shape[:2]
        # 하단 부분 (TAB_REGION_RATIO) 만큼 크롭
        cropped_frame = frame[int(height * (1 - TAB_REGION_RATIO)):, :]
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        # 중복 제거
        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray_frame)
            mean_diff = np.mean(diff)
            if mean_diff < THRESHOLD_DIFF:
                continue

        frame_list.append(cropped_frame)
        saved_count += 1
        prev_frame = gray_frame

    cap.release()
    print(f"Frame extraction done: total processed={frame_count}, kept={saved_count}")

    ############################################
    # (F) TAB 영역 추출
    ############################################
    tab_images = []
    for frm in frame_list:
        tab_region = extract_tab_region(frm)
        if tab_region is not None:
            tab_images.append(tab_region)

    if tab_images:
        print(f"Total TAB regions found: {len(tab_images)}")
    else:
        print("No valid TAB regions were detected in any frame.")

    ############################################
    # (G) 이미지 병합
    ############################################
    final_image = merge_images(tab_images)
    merged_image_path = os.path.join(folder_path, "merged_tabs.png")

    if final_image is not None:
        cv2.imwrite(merged_image_path, final_image)
        print("Merged image saved successfully.")
    else:
        print("No valid image to save.")

    ############################################
    # (H) PDF로 저장
    ############################################
    pdf_output_path = os.path.join(folder_path, "output.pdf")
    save_images_to_pdf(tab_images, pdf_output_path, temp_folder)

    print("All done!")
