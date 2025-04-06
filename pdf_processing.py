# pdf_processing.py
from pathlib import Path
import fitz
from pdf2image import convert_from_path
from google.cloud import vision
import io
import re

def extract_text_with_vision(pdf_path, num_lines):
    """Extracts text from a PDF file using Google Cloud Vision API."""
    images = convert_from_path(pdf_path, first_page=1, last_page=1)
    image = images[0]

    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    content = image_bytes.getvalue()

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.text_annotations:
        text = response.text_annotations[0].description
        lines = text.strip().splitlines()
        if num_lines:
            return "".join(lines[:num_lines])
        return text
    return ""

def extract_text_with_fitz(pdf_path, num_lines):
    """Extracts text from a PDF file using fitz."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            if doc.page_count > 0:
                first_page = doc[0]
                text = first_page.get_text()
                if num_lines:
                    return "".join(text.strip().splitlines()[:num_lines])  
                return text
            return ""
    except Exception as e:
        print(f"Error opening PDF with fitz: {e}")
        return ""

def extract_text_from_pdf(pdf_path, num_lines):
    """Extracts text from a PDF file using fitz and Tesseract OCR."""
    text = extract_text_with_fitz(pdf_path, num_lines)
    if text.strip():
        print(f"Successfully parsed {pdf_path} with fitz")
        return text
    print(f"Error with fitz on {pdf_path}, trying Google cloud vision")
    text = extract_text_with_vision(pdf_path, num_lines)
    if text.strip():
        print(f"Successfully parsed {pdf_path} with Google cloud vision")
    return text    

def is_test(pdf_path):
    """Checks if the PDF file is actually a test."""
    text = extract_text_from_pdf(pdf_path, num_lines=60)
    keywords = ["מבחן", "מבחנים", "בחינה", "מועד", "סמסטר", "שנה", "תשע", "תשפ", "נבחנים"]
    matches = [keyword for keyword in keywords if keyword in text]
    return len(matches) >= 2

def is_test_folder(folder_name: str):
    """Checks if the folder name contains the word 'מבחן' or 'בוחן'."""
    return bool(re.search(r"(מבח[ןנ]|בוח[ןנ])", folder_name))