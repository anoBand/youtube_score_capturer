import cv2
import numpy as np
import os
from typing import Optional, List

def parse_time(value: Optional[str]) -> Optional[float]:
    """
    None -> None
    정수/실수 형태 -> float(초)
    'mm:ss' 형태 -> (mm * 60 + ss)
    """
    if value is None or value.strip() == '':
        return None
    if ':' in value:
        parts = value.split(':')
        return int(parts[0]) * 60 + float(parts[1])
    return float(value)

def extract_tab_region(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    프레임에서 가장 큰 컨투어 영역(악보)을 찾아 잘라낸다.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Canny 엣지 검출을 사용하여 좀 더 명확한 외곽선을 찾도록 개선
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # 가장 큰 컨투어 선택
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        # 추출된 영역이 너무 작지 않은지 확인 (노이즈 방지)
        if w > 50 and h > 50:
            return frame[y:y + h, x:x + w]
    return None

def process_video_frames(video_path: str, output_dir: str, params: dict) -> List[str]:
    """OpenCV로 영상에서 악보 이미지를 추출하고 처리하여 이미지 파일 경로 리스트를 반환합니다."""
    print("Starting video processing...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("비디오 파일을 열 수 없습니다.")

    # 파라미터 추출
    start_time = parse_time(params.get('start_time'))
    end_time = parse_time(params.get('end_time'))
    threshold = float(params.get('threshold', 5.0))
    x_start_percent = float(params.get('x_start', 0.0)) / 100
    x_end_percent = float(params.get('x_end', 100.0)) / 100
    y_start_percent = float(params.get('y_start', 0.0)) / 100
    y_end_percent = float(params.get('y_end', 100.0)) / 100
    transition_sec = float(params.get('transition_sec', 2.0))

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0

    if start_time and start_time > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    effective_end_time = end_time if (end_time and end_time < video_duration) else video_duration

    print(f"Analyzing from {start_time or 0:.2f}s to {effective_end_time:.2f}s")

    prev_frame_gray = None
    stable_frames = []
    processed_image_paths = []
    
    is_in_transition = False
    stable_time_counter = 0.0
    last_pos_sec = start_time or 0

    while True:
        current_pos_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if current_pos_sec > effective_end_time:
            break

        ret, frame = cap.read()
        if not ret:
            break

        dt = current_pos_sec - last_pos_sec
        last_pos_sec = current_pos_sec

        height, width, _ = frame.shape
        crop_rect = (
            int(width * x_start_percent),
            int(width * x_end_percent),
            int(height * y_start_percent),
            int(height * y_end_percent)
        )
        cropped_frame = frame[crop_rect[2]:crop_rect[3], crop_rect[0]:crop_rect[1]]
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        if prev_frame_gray is not None:
            diff = cv2.absdiff(prev_frame_gray, gray_frame)
            mean_diff = np.mean(diff)

            if mean_diff > threshold:
                is_in_transition = True
                stable_time_counter = 0.0
            else:
                if is_in_transition:
                    stable_time_counter += dt
                    if stable_time_counter >= transition_sec:
                        stable_frames.append(cropped_frame)
                        is_in_transition = False
        else:
            # 첫 프레임은 바로 추가
            stable_frames.append(cropped_frame)

        prev_frame_gray = gray_frame

    cap.release()
    print(f"Found {len(stable_frames)} stable frames.")

    # 안정된 프레임에서 악보 영역 추출
    for i, frame in enumerate(stable_frames):
        tab_region = extract_tab_region(frame)
        if tab_region is not None:
            img_path = os.path.join(output_dir, f'frame_{i:04d}.png')
            cv2.imwrite(img_path, tab_region)
            processed_image_paths.append(img_path)
    
    print(f"Extracted {len(processed_image_paths)} tab images.")
    return processed_image_paths
