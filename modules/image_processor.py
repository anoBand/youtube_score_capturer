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
    """
    영상에서 악보 프레임을 최적화된 방식으로 추출합니다.

    최적화 포인트:
    1. cap.set() 대신 cap.grab()을 사용하여 프레임 건너뛰기 속도 개선.
    2. 마스크 연산 시 불필요한 복사를 줄이고 비트 연산 최적화.
    3. 메모리 효율을 위해 대형 객체 재사용.
    """
    print(f"🚀 Optimized Processing Start: Threshold={threshold}, Interval={frame_interval_sec}s")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file.")

    try:
        # 1. 좌표 및 시간 초기 설정
        x_s, x_e = x_start / 100.0, x_end / 100.0
        y_s, y_e = y_start / 100.0, y_end / 100.0

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        start_f = int(start_time * fps) if start_time else 0
        end_f = int(end_time * fps) if end_time else total_frames
        frame_step = max(int(fps * frame_interval_sec), 1)

        # 시작 지점으로 이동 (최초 1회는 set 사용)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
        current_frame = start_f

        processed_image_paths = []
        last_binary_frame = None
        last_dilated_mask = None

        # Local environment: limit removed
        # MAX_IMAGES = 200
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        while current_frame < end_f:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            # 크롭 영역 계산 및 유효성 검사
            y1, y2 = int(h * y_s), int(h * y_e)
            x1, x2 = int(w * x_s), int(w * x_e)

            cropped = frame[y1:y2, x1:x2]
            if cropped.size == 0:
                # 다음 구간까지 grab()으로 건너뛰기
                for _ in range(frame_step - 1):
                    cap.grab()
                current_frame += frame_step
                continue

            # =========================================================
            # [최적화된 알고리즘 로직]
            # =========================================================

            # 1. HSV 변환 및 채도/명도 기반 마스킹 (메모리 재사용 고려)
            hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
            s_channel = hsv[:, :, 1]
            v_channel = hsv[:, :, 2]

            # 채도 10 이상 & 명도 50 이상 영역 추출
            _, s_mask = cv2.threshold(s_channel, 10, 255, cv2.THRESH_BINARY)
            _, v_mask = cv2.threshold(v_channel, 50, 255, cv2.THRESH_BINARY)
            color_mask = cv2.bitwise_and(s_mask, v_mask)

            # 모폴로지 및 팽창 (커널 연산 통합)
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
            dilated_mask = cv2.dilate(color_mask, kernel, iterations=2)  # 3회에서 2회로 조정 (성능)

            # 2. 그레이스케일 변환 및 하이라이트 제거
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            # 마스크 영역을 흰색으로 덮어씀 (Inpainting 대체)
            gray[dilated_mask > 0] = 255

            # 3. 이진화
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

            # 4. 변화량 계산 (XOR 대신 absdiff 사용 - 속도면에서 유사하나 직관적)
            should_save = False
            if last_binary_frame is None:
                should_save = True
            else:
                diff = cv2.absdiff(last_binary_frame, binary)

                # 가변 영역(바 이동 경로) 무시
                unstable_region = cv2.bitwise_or(last_dilated_mask, dilated_mask)
                diff[unstable_region > 0] = 0

                # 평균 변화량 계산 (전체 면적 대비 변화율)
                diff_score = np.mean(diff)

                if diff_score > threshold:
                    should_save = True

            if should_save:
                img_path = os.path.join(output_dir, f'frame_{len(processed_image_paths):04d}.png')
                cv2.imwrite(img_path, cropped)
                processed_image_paths.append(img_path)

                last_binary_frame = binary
                last_dilated_mask = dilated_mask

                # Local environment: limit removed
                # if len(processed_image_paths) >= MAX_IMAGES:
                #     break

            # 핵심: 다음 분석 프레임까지 순차적으로 grab() 하여 속도 향상
            # cap.set()을 반복하는 것보다 cap.grab()이 프레임 간격이 짧을 때 훨씬 빠름
            for _ in range(frame_step - 1):
                if not cap.grab():
                    break
            current_frame += frame_step

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise e
    finally:
        cap.release()

    print(f"✅ Extracted {len(processed_image_paths)} images.")
    return processed_image_paths


def get_single_frame_as_bytes(stream_url, time_sec):
    """미리보기를 위한 단일 프레임 추출 (최적화)"""
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    target_frame = int(time_sec * fps)

    # 특정 시점으로 한 번만 이동
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()

    if ret:
        # JPEG 압축 품질 조절로 네트워크 전송 속도 향상
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            return io.BytesIO(buffer)
    return None