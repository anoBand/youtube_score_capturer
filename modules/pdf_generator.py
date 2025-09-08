# modules/pdf_generator.py

import io
from fpdf import FPDF
from PIL import Image
from typing import List, Union

# --- 변경점 1: 반환 타입을 io.BytesIO로 명시하고, output_path 인자 제거 ---
def create_pdf_from_images(image_paths: List[str]) -> Union[io.BytesIO, None]:
    # Merges a list of image file paths into a PDF in memory.
    if not image_paths:
        print("No images provided for PDF generation.")
        return None

    print(f"Starting PDF generation from {len(image_paths)} images.")
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    margin = 10
    pdf_page_width = 210 - 2 * margin
    pdf_page_height = 297 - 2 * margin
    current_y = margin
    image_spacing = 2  # Space between images in mm

    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                width_px, height_px = img.size

            aspect_ratio = width_px / height_px
            img_width_mm = pdf_page_width
            img_height_mm = img_width_mm / aspect_ratio

            if img_height_mm > pdf_page_height:
                img_height_mm = pdf_page_height
                img_width_mm = img_height_mm * aspect_ratio

            if current_y + img_height_mm > (297 - margin):
                pdf.add_page()
                current_y = margin

            x_pos = (210 - img_width_mm) / 2
            pdf.image(img_path, x=x_pos, y=current_y, w=img_width_mm, h=img_height_mm)
            current_y += img_height_mm + image_spacing

        except Exception as e:
            print(f"Could not process image {img_path}: {e}")
            continue
    
    # --- 변경점 2: PDF를 파일이 아닌 메모리(Bytes)로 출력하여 반환 ---
    if pdf.page_no() > 0:
        # pdf.output()을 통해 메모리에 PDF 데이터를 생성하고 BytesIO 객체로 감싸서 반환
        pdf_bytes = pdf.output(dest='S')
        print("PDF successfully generated in memory.")
        return io.BytesIO(pdf_bytes)
    else:
        print("PDF generation failed. No images were processed.")
        return None