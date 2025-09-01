from fpdf import FPDF
from PIL import Image
import os
from typing import List

def create_pdf_from_images(image_paths: List[str], output_dir: str, filename: str = "output.pdf") -> str:
    """이미지 파일 경로 리스트를 받아 PDF로 병합합니다."""
    print(f"Starting PDF generation from {len(image_paths)} images.")
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)

    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                width_px, height_px = img.size

            # A4 page dimensions in mm (with margin)
            margin = 10
            pdf_page_width = 210 - 2 * margin
            pdf_page_height = 297 - 2 * margin

            # Calculate image aspect ratio
            aspect_ratio = width_px / height_px

            # Calculate scaled image dimensions to fit page width
            img_width_mm = pdf_page_width
            img_height_mm = img_width_mm / aspect_ratio

            # If scaled height is too large, scale based on height instead
            if img_height_mm > pdf_page_height:
                img_height_mm = pdf_page_height
                img_width_mm = img_height_mm * aspect_ratio

            pdf.add_page()
            # Center the image on the page
            x_pos = (210 - img_width_mm) / 2
            y_pos = (297 - img_height_mm) / 2
            pdf.image(img_path, x=x_pos, y=y_pos, w=img_width_mm, h=img_height_mm)

        except Exception as e:
            print(f"Could not process image {img_path}: {e}")
            continue

    pdf_path = os.path.join(output_dir, filename)
    if len(pdf.pages) > 0:
        pdf.output(pdf_path)
        print(f"PDF successfully created at: {pdf_path}")
    else:
        raise RuntimeError("PDF 생성에 실패했습니다. 처리할 이미지가 없습니다.")

    return pdf_path
