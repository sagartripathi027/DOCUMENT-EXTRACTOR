import cv2
import numpy as np
import pytesseract
import re
import os
import shutil
from pdf2image import convert_from_path
from PIL import Image
if os.name == "nt":
    _default_tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_tess):
        pytesseract.pytesseract.tesseract_cmd = _default_tess
else:
    _linux_tess = shutil.which("tesseract")
    if _linux_tess:
        pytesseract.pytesseract.tesseract_cmd = _linux_tess
POPPLER_PATH = r'C:\poppler\poppler-26.02.0\Library\bin'
def _get_poppler_path():
    if os.name == "nt" and os.path.exists(POPPLER_PATH):
        return POPPLER_PATH
    return None
def _deskew(gray):
    try:
        coords = np.column_stack(np.where(gray < 255))

        if coords.shape[0] < 10:
            return gray

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.1 or abs(angle) > 45:
            return gray

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        rotated = cv2.warpAffine(
            gray,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return rotated

    except Exception:
        return gray


def _sharpen(gray):
    try:
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])

        return cv2.filter2D(gray, -1, kernel)

    except Exception:
        return gray
def preprocess_image(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not loaded properly.")

    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#  Noise removal
    gray = cv2.fastNlMeansDenoising(gray, h=10)

#  Deskew
    gray = _deskew(gray)

#  Contrast boost (IMPORTANT)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

#  Optional sharpening
    gray = _sharpen(gray)

#  Adaptive threshold (fix for light background)
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15, 4
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

#  Noise removal
    gray = cv2.fastNlMeansDenoising(gray, h=10)

#  Deskew
    gray = _deskew(gray)

# CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

#  Optional sharpening
    gray = _sharpen(gray)

# Blur
    gray = cv2.medianBlur(gray, 3)

# Threshold
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15, 4
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
        try:
            poppler_path = _get_poppler_path()

            if poppler_path:
                pages = convert_from_path(
                    file_path,
                    poppler_path=poppler_path
                )
            else:
                pages = convert_from_path(file_path)

        except Exception:
            return ''

        all_text = ''

        for page in pages:
            try:
                processed = preprocess_pil_image(page)
                raw_text = pytesseract.image_to_string(
                    processed,
                    config=config
                )

                all_text += raw_text + ' '

            except Exception:
                continue

        return clean_text(all_text)

    else:
        try:
            processed = preprocess_image(file_path)

            raw_text = pytesseract.image_to_string(
                processed,
                config=config
            )

            return clean_text(raw_text)

        except Exception:
            return ''


if __name__ == "__main__":
    path = "test_image.png"
    print(extract_text(path))