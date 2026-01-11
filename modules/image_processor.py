# modules/image_processor.py

import cv2
import io
import numpy as np
import os
from typing import Optional, List

def process_video_frames(
        video_path: str, output_dir: str,
        start_time: Optional[int], end_time: Optional[int],
        x_start: int, x_end: int, y_start: int, y_end: int,
        threshold: float, frame_interval_sec: float = 1.0
) -> List[str]:
    print("🚀 Starting optimized video processing...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file.")

    try:
        # [기존] 좌표 변환 로직 동일
        x_start_p, x_end_p = x_start / 100.0, x_end / 100.0
        y_start_p, y_end_p = y_start / 100.0, y_end / 100.0

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 시작 시간 설정 (Seeking)
        current_frame = int(start_time * fps) if start_time else 0
        end_frame = int(end_time * fps) if end_time else total_frames
        frame_step = int(fps * frame_interval_sec) or 1

        processed_image_paths = []
        last_saved_frame_gray = None
        MAX_IMAGES = 200  # [개선] 서버 보호를 위한 최대 이미지 생성 제한

        while current_frame < end_frame:
            # [개선] 다음 처리할 프레임으로 바로 점프 (성능 향상의 핵심)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret: break

            # [기존] 크롭 및 그레이스케일 변환 로직 동일
            h, w, _ = frame.shape
            cropped = frame[int(h * y_start_p):int(h * y_end_p), int(w * x_start_p):int(w * x_end_p)]
            if cropped.size == 0:
                current_frame += frame_step
                continue

            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

            # 변화량 체크 로직
            should_save = False
            if last_saved_frame_gray is None:
                should_save = True
            else:
                diff = cv2.absdiff(last_saved_frame_gray, gray)
                if np.mean(diff) > threshold:
                    should_save = True

            if should_save:
                img_path = os.path.join(output_dir, f'frame_{len(processed_image_paths):04d}.png')
                cv2.imwrite(img_path, cropped)
                processed_image_paths.append(img_path)
                last_saved_frame_gray = gray

                # [개선] 무한 이미지 생성 방지
                if len(processed_image_paths) >= MAX_IMAGES:
                    print(f"⚠️ Reached max image limit ({MAX_IMAGES}). Stopping.")
                    break

            current_frame += frame_step

    finally:
        cap.release()  # [개선] 어떤 상황에서도 리소스 해제 보장

    print(f"✅ Extracted {len(processed_image_paths)} images.")
    return processed_image_paths

def get_single_frame_as_bytes(stream_url, time_sec):
    """스트림 주소에서 특정 시점의 프레임을 캡처하여 BytesIO 객체로 반환합니다."""
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(time_sec * fps))

    ret, frame = cap.read()
    cap.release()

    if ret:
        # 이미지를 JPG 형식으로 인코딩
        success, buffer = cv2.imencode('.jpg', frame)
        if success:
            # Flask의 send_file이 바로 읽을 수 있도록 BytesIO로 래핑
            return io.BytesIO(buffer)

    return None