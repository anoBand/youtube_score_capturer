import io
from fpdf import FPDF
from PIL import Image
from typing import List, Union


def create_pdf_from_images(image_paths: List[str]) -> Union[io.BytesIO, None]:
    if not image_paths:
        print("No images provided for PDF generation.")
        return None

    print(f"📄 Starting PDF generation: {len(image_paths)} images.")

    # A4 사이즈 PDF 생성
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)

    # 첫 페이지 추가
    pdf.add_page()

    margin = 10
    page_width = 210
    page_height = 297
    max_w = page_width - (2 * margin)
    max_h = page_height - (2 * margin)

    # [수정 1] 현재 이미지가 그려질 Y 위치 추적 변수 초기화
    current_y = margin
    image_spacing = 5  # 이미지 사이의 간격 (mm)

    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                w_px, h_px = img.size

            # 비율 유지하며 가로 길이를 페이지 너비(max_w)에 맞춤
            aspect = w_px / h_px
            display_w = max_w
            display_h = display_w / aspect

            # (예외 처리) 만약 이미지 하나가 페이지 전체 높이보다 크다면 줄임
            if display_h > max_h:
                display_h = max_h
                display_w = display_h * aspect

            # [수정 2] 현재 페이지에 공간이 부족하면 새 페이지 추가
            # (현재 위치 + 이미지 높이)가 (페이지 높이 - 하단 여백)을 넘는지 확인
            if current_y + display_h > (page_height - margin):
                pdf.add_page()
                current_y = margin  # Y 위치를 다시 맨 위로 초기화

            # [수정 3] 중앙 정렬 위치 계산 (X는 중앙, Y는 current_y 사용)
            x_pos = (page_width - display_w) / 2

            # 이미지 그리기
            pdf.image(img_path, x=x_pos, y=current_y, w=display_w, h=display_h)

            # [수정 4] 다음 이미지를 위해 Y 위치 갱신 (이미지 높이 + 간격)
            current_y += display_h + image_spacing

        except Exception as e:
            print(f"⚠️ Error processing {img_path}: {e}")
            continue

    if pdf.page_no() > 0:
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_output = pdf_output.encode('latin1')

        return io.BytesIO(pdf_output)

    return None