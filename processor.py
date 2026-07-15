import cv2
import numpy as np
import pytesseract
import re
import os

from pdf2image import convert_from_path
from PIL import Image

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r'C:\poppler\poppler-26.02.0\Library\bin'


def preprocess_image(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not loaded properly.")

    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #  Contrast boost (IMPORTANT)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    #  Adaptive threshold (fix for light background)
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    #  Invert (handles light text)
    processed = cv2.bitwise_not(processed)

    return processed


def preprocess_pil_image(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔥 Auto invert
    if np.mean(gray) < 127:
        gray = cv2.bitwise_not(gray)

    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # Blur
    gray = cv2.medianBlur(gray, 3)

    # Threshold
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Dilation
    kernel = np.ones((1,1), np.uint8)
    processed = cv2.dilate(processed, kernel, iterations=1)

    return processed


def clean_text(text):
    """
    Clean OCR output
    """
    text = text.replace("\n", " ")
    text = re.sub(r'[^a-zA-Z0-9@.$:/\-\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_text(file_path):
    """
    Full OCR pipeline — handles both images and PDFs
    """
    config = r'--oem 3 --psm 6'

    if file_path.lower().endswith('.pdf'):
        # Convert each PDF page to image, then OCR
        if os.name == "nt":
            pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        else:
            pages = convert_from_path(file_path)
        all_text = ''
        for page in pages:
            processed = preprocess_pil_image(page)
            raw_text = pytesseract.image_to_string(processed, config=config)
            all_text += raw_text + ' '
        return clean_text(all_text)

    else:
        # Original image pipeline unchanged
        processed = preprocess_image(file_path)
        raw_text = pytesseract.image_to_string(processed, config=config)
        return clean_text(raw_text)


# Optional test run
if __name__ == "__main__":
    path = "test_image.png"
    print(extract_text(path))