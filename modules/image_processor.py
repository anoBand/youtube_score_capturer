# modules/image_processor.py

import cv2
import numpy as np
import os
from typing import Optional, List

# --- 변경점 1: 함수 정의에 start_time, end_time 추가 ---
def process_video_frames(
    video_path: str, output_dir: str, 
    start_time: Optional[int], end_time: Optional[int], 
    x_start: int, x_end: int, y_start: int, y_end: int, 
    threshold: float, transition_sec: float, frame_interval_sec: float = 1.0
) -> List[str]:
    # Extracts and processes sheet music images from a video, returns a list of image paths.
    print("Starting video processing...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file.")

    # Convert percentages to ratios
    x_start_percent = x_start / 100.0
    x_end_percent = x_end / 100.0
    y_start_percent = y_start / 100.0
    y_end_percent = y_end / 100.0

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30 # Assume a default fps
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0
    frame_interval_frames = int(fps * frame_interval_sec)
    if frame_interval_frames < 1:
        frame_interval_frames = 1

    # --- 변경점 2: 처리 범위 로그 추가 ---
    start_log = f"{start_time}s" if start_time is not None else "start"
    end_log = f"{end_time}s" if end_time is not None else "end"
    print(f"Analyzing video with duration: {video_duration:.2f}s. Processing range: [{start_log} to {end_log}].")

    prev_frame_gray = None
    saved_images = []
    processed_image_paths = []
    last_saved_frame_gray = None

    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- 변경점 3: start_time과 end_time을 기준으로 프레임 처리 여부 결정 ---
        current_time_sec = frame_number / fps

        # start_time 이전의 프레임은 건너뛰기
        if start_time is not None and current_time_sec < start_time:
            frame_number += 1
            continue

        # end_time 이후의 프레임은 루프 종료
        if end_time is not None and current_time_sec > end_time:
            break
        # --- 여기까지 변경점 3 ---

        if frame_number % frame_interval_frames == 0:
            height, width, _ = frame.shape
            crop_rect = (
                int(width * x_start_percent),
                int(width * x_end_percent),
                int(height * y_start_percent),
                int(height * y_end_percent)
            )
            cropped_frame = frame[crop_rect[2]:crop_rect[3], crop_rect[0]:crop_rect[1]]
            
            if cropped_frame.size == 0:
                frame_number += 1
                continue
                
            gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

            if prev_frame_gray is None:
                prev_frame_gray = gray_frame
                last_saved_frame_gray = gray_frame
                img_path = os.path.join(output_dir, f'frame_{len(saved_images):04d}.png')
                cv2.imwrite(img_path, cropped_frame)
                saved_images.append(cropped_frame)
                processed_image_paths.append(img_path)
            else:
                diff_with_last_saved = cv2.absdiff(last_saved_frame_gray, gray_frame)
                mean_diff = np.mean(diff_with_last_saved)

                if mean_diff > threshold:
                    last_saved_frame_gray = gray_frame
                    img_path = os.path.join(output_dir, f'frame_{len(saved_images):04d}.png')
                    cv2.imwrite(img_path, cropped_frame)
                    saved_images.append(cropped_frame)
                    processed_image_paths.append(img_path)

            prev_frame_gray = gray_frame

        frame_number += 1

    cap.release()
    print(f"Extracted {len(processed_image_paths)} images.")
    return processed_image_paths