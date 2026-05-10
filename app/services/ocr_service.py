# ============================================================
#  ocr_service.py — Extract text from Images and PDFs
#
#  OCR = Optical Character Recognition
#  It reads text from images just like a human would.
#
#  Tools used:
#    - EasyOCR  : AI-based OCR (more accurate)
#    - Tesseract: Traditional OCR (backup option)
#    - PyMuPDF  : Read text from PDF files
# ============================================================

import os
import numpy as np
import fitz          # PyMuPDF — for reading PDFs
import pytesseract   # Traditional OCR backup
from PIL import Image, ImageEnhance, ImageFilter

# We load EasyOCR only once (it's a heavy AI model)
# Loading it every time would be very slow
_easy_ocr_reader = None

def _load_easyocr():
    """Load EasyOCR model into memory (only happens once)."""
    global _easy_ocr_reader
    if _easy_ocr_reader is None:
        import easyocr
        print("Loading EasyOCR model... (this takes ~30 seconds first time)")
        _easy_ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        print("EasyOCR ready!")
    return _easy_ocr_reader


def _improve_image(img):
    """
    Make the image clearer so OCR works better.
    Steps:
      1. Convert to grayscale
      2. Increase contrast (makes text stand out)
      3. Sharpen edges
    """
    img = img.convert("L")                         # Step 1: Grayscale
    img = ImageEnhance.Contrast(img).enhance(2.0)  # Step 2: More contrast
    img = img.filter(ImageFilter.SHARPEN)           # Step 3: Sharpen
    return img.convert("RGB")


def extract_text(file_path):
    """
    Main function — call this to get text from any file.

    It automatically detects if it's a PDF or image
    and uses the right method.

    Returns: A string with all the extracted text
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    # Get file extension (.pdf, .png, etc.)
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return _extract_from_pdf(file_path)
    else:
        return _extract_from_image(file_path)


def _extract_from_pdf(file_path):
    """
    Extract text from a PDF file.

    Two cases:
    1. PDF has real text (like a digital invoice) → just read it directly
    2. PDF is a scanned image → render each page and run OCR on it
    """
    doc = fitz.open(file_path)
    all_pages_text = []

    for page_number, page in enumerate(doc):
        # Try to get text directly from the PDF
        text = page.get_text("text").strip()

        if len(text) > 30:
            # Great! This page has real text — no OCR needed
            all_pages_text.append(text)
        else:
            # This page is a scanned image — need OCR
            # Render page as a high-quality image (300 DPI)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = _run_ocr(img)
            all_pages_text.append(page_text)

    doc.close()
    return "\n\n".join(all_pages_text)


def _extract_from_image(file_path):
    """Extract text from an image file (PNG, JPG, etc.)"""
    img = Image.open(file_path).convert("RGB")
    img = _improve_image(img)  # Make it clearer first
    return _run_ocr(img)


def _run_ocr(img):
    """
    Run OCR on an image.
    Tries EasyOCR first (better), falls back to Tesseract if it fails.
    """
    try:
        reader = _load_easyocr()
        # Convert PIL Image to numpy array (EasyOCR needs this format)
        img_array = np.array(img)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        return "\n".join(results)

    except Exception as error:
        print(f"EasyOCR failed: {error}. Trying Tesseract backup...")
        try:
            return pytesseract.image_to_string(img, config="--oem 3 --psm 6")
        except Exception:
            return ""  # If both fail, return empty string
