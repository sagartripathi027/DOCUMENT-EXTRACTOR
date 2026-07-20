import cv2
import numpy as np
import pytesseract
import re
import os
import shutil
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
if os.name == "nt":
    _default_tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_tess):
        pytesseract.pytesseract.tesseract_cmd = _default_tess
else:
    _linux_tess = shutil.which("tesseract")
    if _linux_tess:
        pytesseract.pytesseract.tesseract_cmd = _linux_tess
POPPLER_PATH = os.getenv("POPPLER_PATH")
def _get_poppler_path():
    if POPPLER_PATH and os.path.exists(POPPLER_PATH):
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

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return processed

def preprocess_pil_image(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

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

    config = r'--oem 3 --psm 3'

    # PDF
    if file_path.lower().endswith(".pdf"):
        try:
            poppler_path = _get_poppler_path()

            if poppler_path:
                pages = convert_from_path(
                    file_path,
                    dpi=120,
                    first_page=1,
                    last_page=1,
                    poppler_path=poppler_path
                )
            else:
                pages = convert_from_path(
                    file_path,
                    dpi=120,
                    first_page=1,
                    last_page=1
                )

            all_text = ""

            for page in pages:
                processed = preprocess_pil_image(page)
                raw_text = pytesseract.image_to_string(
                    processed,
                    config=config
                )
                all_text += raw_text + " "

            return clean_text(all_text)

        except Exception as e:
            print("PDF Error:", e)
            return ""

    # Image
    else:
        try:
            processed = preprocess_image(file_path)

            raw_text = pytesseract.image_to_string(
                processed,
                config=config
            )

            return clean_text(raw_text)

        except Exception as e:
            print("Image Error:", e)
            return ""


if __name__ == "__main__":
    path = "test_image.png"
    print(extract_text(path))