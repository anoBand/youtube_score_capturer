# modules/pdf_generator.py

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

    margin = 10
    page_width = 210
    page_height = 297
    max_w = page_width - (2 * margin)
    max_h = page_height - (2 * margin)

    for img_path in image_paths:
        try:
            pdf.add_page()

            with Image.open(img_path) as img:
                w_px, h_px = img.size

            # 비율 유지하며 페이지에 꽉 차게 계산
            aspect = w_px / h_px
            display_w = max_w
            display_h = display_w / aspect

            # 만약 계산된 높이가 페이지보다 길면 높이에 맞춤
            if display_h > max_h:
                display_h = max_h
                display_w = display_h * aspect

            # 중앙 정렬 위치 계산
            x_pos = (page_width - display_w) / 2
            y_pos = (page_height - display_h) / 2

            pdf.image(img_path, x=x_pos, y=y_pos, w=display_w, h=display_h)

        except Exception as e:
            print(f"⚠️ Error processing {img_path}: {e}")
            continue

    if pdf.page_no() > 0:
        # dest='S'는 바이트 문자열을 반환합니다.
        pdf_output = pdf.output(dest='S')
        # fpdf 버전에 따라 바이트 변환이 필요할 수 있습니다 (pyfpdf vs fpdf2)
        if isinstance(pdf_output, str):
            pdf_output = pdf_output.encode('latin1')

        return io.BytesIO(pdf_output)

    return None