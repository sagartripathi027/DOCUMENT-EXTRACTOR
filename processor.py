import cv2
import numpy as np
import pytesseract
import re

# ✅ Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\SAGAR TRIPATHI\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def preprocess_image(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not loaded properly. Check file path or format.")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔥 Improve contrast (helps OCR a lot)
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

    # Adaptive threshold
    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # Noise removal
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.medianBlur(processed, 3)

    return processed


def clean_text(text):
    text = text.replace("\n", " ")
    
    # keep useful OCR characters
    text = re.sub(r'[^a-zA-Z0-9@.$:/\-\s]', ' ', text)

    # remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_text(image_path):
    processed = preprocess_image(image_path)

    # 🔥 Better OCR config
    config = r'--oem 3 --psm 6'

    text = pytesseract.image_to_string(processed, config=config)

    return clean_text(text)