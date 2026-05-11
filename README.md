# AI Doc Extractor

## 📌 Overview

OCR-based system to extract structured text from images and PDFs.

---

## 🚀 Features

* Extract text from images and PDF documents
* Image preprocessing (denoising, thresholding)
* Flask backend for file upload and processing

---

## 🛠 Tech Stack

* Python
* Flask
* Tesseract OCR
* OpenCV

---

## ⚙️ Setup (Important)

### Requirements

* Python 3.8+

### Install Tesseract OCR

* **Windows:** Install and add to PATH
* **Linux:**

```bash
sudo apt install tesseract-ocr
```

* **Mac:**

```bash
brew install tesseract
```

---

## 📊 Results

* Achieved ~90% accuracy on 80+ test documents

---

## 📸 Demo

### 🖼️ Input Document

User uploads a document image.

### 📤 Extracted Output

The system processes the image and extracts structured text.

<p align="center">
  <img src="image/demo.png" width="700">
</p>

This demonstrates the OCR pipeline converting raw document images into usable structured data.

---

## ⚙️ How to Run

```bash
git clone https://github.com/sagartripathi027/DOCUMENT-EXTRACTOR.git
cd DOCUMENT-EXTRACTOR
pip install -r requirements.txt
python app.py
```

---

## 📁 Project Structure

```
app.py
parser.py
processor.py
utils.py
image/
templates/
static/
uploads/
```

---

## 🎯 Workflow

1. User uploads image/PDF
2. Image preprocessing using OpenCV
3. Text extraction using Tesseract OCR
4. Structured data parsing
5. Output displayed via Flask

---

## 📌 Future Improvements

* Improve OCR accuracy with better preprocessing
* Add support for more document formats
* Deploy as a web app

---

## 🙌 Acknowledgment

Built as a practical project to demonstrate OCR + Flask integration.
