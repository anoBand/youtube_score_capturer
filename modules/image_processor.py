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
    영상에서 악보 프레임을 추출합니다.
    [검수 로직 적용]
    1. 하이라이트(유채색) 영역을 완벽히 마스킹하여 '배경'으로 취급합니다.
    2. 이전 프레임과 현재 프레임의 하이라이트 영역을 합쳐 '비교 제외 구역'으로 설정합니다.
    3. 순수 악보(검은 잉크)의 변화만 감지하여 중복을 방지합니다.
    """
    print(f"🚀 Processing: Threshold={threshold}, Interval={frame_interval_sec}s")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file.")

    try:
        # 1. 좌표 정규화
        x_start_p, x_end_p = x_start / 100.0, x_end / 100.0
        y_start_p, y_end_p = y_start / 100.0, y_end / 100.0

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 2. 탐색 구간 설정
        current_frame = int(start_time * fps) if start_time else 0
        end_frame = int(end_time * fps) if end_time else total_frames
        frame_step = int(fps * frame_interval_sec) or 1

        processed_image_paths = []

        # [상태 저장 변수]
        last_binary_frame = None  # 이전 프레임의 이진화 이미지
        last_dilated_mask = None  # 이전 프레임의 하이라이트 마스크

        MAX_IMAGES = 200

        # [마스킹 커널 설정]
        # 5x5 사각형 커널: 노이즈 제거 및 영역 확장에 사용
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        while current_frame < end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret: break

            h, w, _ = frame.shape

            # 3. 사용자 지정 영역 크롭
            cropped = frame[int(h * y_start_p):int(h * y_end_p), int(w * x_start_p):int(w * x_end_p)]
            if cropped.size == 0:
                current_frame += frame_step
                continue

            # =========================================================
            # [알고리즘: Human Check Logic 구현]
            # =========================================================

            # A. 색상 분리 (HSV 변환)
            hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
            s_channel = hsv[:, :, 1]  # 채도
            v_channel = hsv[:, :, 2]  # 명도

            # B. 정교한 하이라이트 마스크 생성
            # 조건 1: 채도가 10 이상 (아주 연한 파스텔톤도 감지)
            _, s_mask = cv2.threshold(s_channel, 10, 255, cv2.THRESH_BINARY)

            # 조건 2: 명도가 50 이상 (검은색 잉크는 마스킹하지 않도록 보호)
            _, v_mask = cv2.threshold(v_channel, 50, 255, cv2.THRESH_BINARY)

            # 두 조건을 모두 만족해야 하이라이트임
            color_mask = cv2.bitwise_and(s_mask, v_mask)

            # [추가] 모폴로지 닫기 (Closing): 마스크 내부의 구멍(글자 등)을 메워 덩어리로 만듦
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)

            # C. 마스크 팽창 (Dilation): 경계선 노이즈 제거를 위해 영역을 넓힘 (3회 반복)
            dilated_mask = cv2.dilate(color_mask, kernel, iterations=3)

            # D. 그레이스케일 변환
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

            # E. [Inpainting 효과] 하이라이트 자리를 흰색(255)으로 덮어씀
            # -> 이 과정으로 인해 하이라이트 바는 '흰 종이'가 됩니다.
            gray_no_highlight = gray.copy()
            gray_no_highlight[dilated_mask > 0] = 255

            # F. 이진화 (Binarization)
            # -> 회색조 노이즈를 없애고 0(음표)과 255(배경)만 남깁니다.
            _, binary = cv2.threshold(gray_no_highlight, 200, 255, cv2.THRESH_BINARY)

            # =========================================================

            should_save = False

            if last_binary_frame is None:
                should_save = True
            else:
                # G. 변화량 계산 (검수 로직의 핵심)

                # 1. 두 이미지의 차이 계산 (XOR 연산)
                diff = cv2.absdiff(last_binary_frame, binary)

                # 2. [핵심] "공통 가시 영역"만 비교
                # 이전 프레임의 바 위치(last_mask)와 현재 프레임의 바 위치(curr_mask)를 합침
                # 이 합쳐진 영역(unstable_region)은 음표가 가려졌다 나타나는 곳이므로 비교에서 제외
                unstable_region = cv2.bitwise_or(last_dilated_mask, dilated_mask)

                # 3. 불안정 영역의 차이 값을 0으로 강제 초기화 (무시)
                diff[unstable_region > 0] = 0

                # 4. 남은 영역(안정적인 악보)에서의 변화율만 계산
                diff_score = np.mean(diff)

                # 디버깅용 로그 (필요시 해제)
                # print(f"Frame {current_frame}: Diff Score = {diff_score:.2f}")

                if diff_score > threshold:
                    should_save = True

            if should_save:
                img_path = os.path.join(output_dir, f'frame_{len(processed_image_paths):04d}.png')

                # 사용자를 위해 '원본(컬러)' 이미지를 저장합니다.
                # (분석은 흑백으로 했지만, 결과물은 깨끗한 원본이어야 함)
                cv2.imwrite(img_path, cropped)

                processed_image_paths.append(img_path)

                # 다음 비교를 위해 현재 상태 저장
                last_binary_frame = binary
                last_dilated_mask = dilated_mask

                if len(processed_image_paths) >= MAX_IMAGES:
                    print(f"⚠️ Reached max image limit ({MAX_IMAGES}). Stopping.")
                    break

            current_frame += frame_step

    except Exception as e:
        print(f"Error during processing: {e}")
        raise e
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