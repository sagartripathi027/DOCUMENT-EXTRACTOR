import cv2
import numpy as np
import pytesseract
import re
from pdf2image import convert_from_path
from PIL import Image

# ✅ Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\SAGAR TRIPATHI\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# ✅ Set Poppler path (update this to your actual path)
# Replace with YOUR actual path where pdftoppm.exe lives
POPPLER_PATH = r'C:\poppler-24.08.0\Library\bin'


def preprocess_image(image_path):
    """
    Preprocess image for better OCR accuracy
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not loaded properly. Check file path or format.")

    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)
    gray = cv2.medianBlur(gray, 3)
    processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return processed


def preprocess_pil_image(pil_img):
    """
    Same preprocessing but accepts a PIL image (used for PDF pages)
    """
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)
    gray = cv2.medianBlur(gray, 3)
    processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

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
    config = r'--oem 3 --psm 11'

    if file_path.lower().endswith('.pdf'):
        # Convert each PDF page to image, then OCR
        pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
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