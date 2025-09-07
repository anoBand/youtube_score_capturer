import io
from fpdf import FPDF
from PIL import Image
import os
from typing import List

def create_pdf_from_images(image_paths: List[str], output_path: str) -> None:
    # Merges a list of image file paths into a PDF, fitting multiple images per page.
    print(f"Starting PDF generation from {len(image_paths)} images.")
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    margin = 10
    pdf_page_width = 210 - 2 * margin
    pdf_page_height = 297 - 2 * margin
    current_y = margin
    image_spacing = 5  # Space between images in mm

    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                width_px, height_px = img.size

            aspect_ratio = width_px / height_px
            img_width_mm = pdf_page_width
            img_height_mm = img_width_mm / aspect_ratio

            if img_height_mm > pdf_page_height: # If a single image is too tall, scale it down
                img_height_mm = pdf_page_height
                img_width_mm = img_height_mm * aspect_ratio

            # Check if the image fits in the remaining space on the current page
            if current_y + img_height_mm > (297 - margin):
                pdf.add_page()
                current_y = margin

            x_pos = (210 - img_width_mm) / 2  # Center horizontally
            pdf.image(img_path, x=x_pos, y=current_y, w=img_width_mm, h=img_height_mm)
            current_y += img_height_mm + image_spacing

        except Exception as e:
            print(f"Could not process image {img_path}: {e}")
            continue

    if len(pdf.pages) > 0:
        pdf.output(output_path)
        print(f"PDF successfully created at: {output_path}")
    else:
        raise RuntimeError("PDF generation failed. No images to process.")