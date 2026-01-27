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
    print("🚀 Starting improved video processing with enhanced highlight masking...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file.")

    try:
        x_start_p, x_end_p = x_start / 100.0, x_end / 100.0
        y_start_p, y_end_p = y_start / 100.0, y_end / 100.0

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        current_frame = int(start_time * fps) if start_time else 0
        end_frame = int(end_time * fps) if end_time else total_frames
        frame_step = int(fps * frame_interval_sec) or 1

        processed_image_paths = []
        last_saved_frame_gray = None
        MAX_IMAGES = 200

        # 팽창 연산을 위한 커널 설정 (테두리 노이즈 제거용)
        kernel = np.ones((5, 5), np.uint8)

        while current_frame < end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret: break

            h, w, _ = frame.shape
            cropped = frame[int(h * y_start_p):int(h * y_end_p), int(w * x_start_p):int(w * x_end_p)]
            if cropped.size == 0:
                current_frame += frame_step
                continue

            # --- [개선] 더욱 강력한 하이라이트 제거 로직 ---
            hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
            s_channel = hsv[:, :, 1]  # 채도
            v_channel = hsv[:, :, 2]  # 명도

            # 1. 채도가 높거나(유채색), 명도가 너무 밝은 영역(바의 중심)을 마스킹
            # 임계값을 30으로 낮추어 더 민감하게 색상을 잡습니다.
            _, color_mask = cv2.threshold(s_channel, 30, 255, cv2.THRESH_BINARY)

            # 2. 팽창(Dilation) 연산: 마스크 영역을 상하좌우로 넓혀서
            # 하이라이트 바의 흐릿한 테두리(Anti-aliasing)까지 확실히 포함시킵니다.
            dilated_mask = cv2.dilate(color_mask, kernel, iterations=1)

            # 3. 그레이스케일 변환 및 마스킹 적용
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            cleaned_gray = gray.copy()
            cleaned_gray[dilated_mask > 0] = 255  # 색상이 있던 자리를 흰색으로 완전히 덮음

            # (선택 사항) 미세한 노이즈 제거를 위한 가우시안 블러
            cleaned_gray = cv2.GaussianBlur(cleaned_gray, (5, 5), 0)
            # --------------------------------------------

            should_save = False
            if last_saved_frame_gray is None:
                should_save = True
            else:
                diff = cv2.absdiff(last_saved_frame_gray, cleaned_gray)
                mean_diff = np.mean(diff)

                # 로그 출력 (디버깅용)
                # print(f"Frame {current_frame}: Mean Diff = {mean_diff:.4f}")

                if mean_diff > threshold:
                    should_save = True

            if should_save:
                img_path = os.path.join(output_dir, f'frame_{len(processed_image_paths):04d}.png')
                cv2.imwrite(img_path, cropped)
                processed_image_paths.append(img_path)
                last_saved_frame_gray = cleaned_gray

                if len(processed_image_paths) >= MAX_IMAGES:
                    print(f"⚠️ Reached max image limit ({MAX_IMAGES}). Stopping.")
                    break

            current_frame += frame_step

    finally:
        cap.release()

    print(f"✅ Extracted {len(processed_image_paths)} images.")
    return processed_image_paths


def get_single_frame_as_bytes(stream_url, time_sec):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(time_sec * fps))
    ret, frame = cap.read()
    cap.release()
    if ret:
        success, buffer = cv2.imencode('.jpg', frame)
        if success:
            return io.BytesIO(buffer)
    return None