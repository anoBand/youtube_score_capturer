import cv2
import numpy as np
import yt_dlp

url = "https://youtu.be/xRB33Ertak0?si=h2W13vggNPXUPHd3"
output_path = "video.mp4"

ydl_opts = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
    "outtmpl": output_path,
    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],  # FFmpeg 사용하여 변환
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

video_path = "video.mp4"
cap = cv2.VideoCapture(video_path)
frame_rate = 1  # 초당 1프레임씩 추출
threshold_diff = 18  # 프레임 차이 비교 임계값
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
    cropped_frame = frame[int(height * (1 - tab_region_ratio)):, :]  # 설정된 비율만큼 하단 추출
    gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)  # 흑백 변환

    if prev_frame is not None:
        diff = cv2.absdiff(prev_frame, gray_frame)
        mean_diff = np.mean(diff)

        if mean_diff < threshold_diff:
            continue

    frame_list.append(cropped_frame)
    prev_frame = gray_frame

# 마지막 프레임 강제 추가
if prev_frame is not None and cropped_frame is not None:
    frame_list.append(cropped_frame)

cap.release()

def extract_tab_region(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    roi = gray[:, :]  # 이미 하단 부분을 받았으므로 그대로 사용

    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)  # 가장 큰 컨투어 선택
        x, y, w, h = cv2.boundingRect(contours[0])
        return frame[y:y + h, x:x + w]

    return None

tab_images = [extract_tab_region(frame) for frame in frame_list if extract_tab_region(frame) is not None]

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
if final_image is not None:
    cv2.imwrite("merged_tabs.png", final_image)
    print("Merged image saved successfully.")
else:
    print("No valid image to save.")
