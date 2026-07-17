# 📄 Document Extractor AI 🚀

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![OCR](https://img.shields.io/badge/OCR-Tesseract-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Deployment](https://img.shields.io/badge/Live-Render-success)

## 🌐 Live Demo
🚀 https://document-extractor-1-frq3.onrender.com

## 📌 Overview

Document Extractor AI is an OCR-based document processing system that converts images and PDF documents into structured data.

The system uses Tesseract OCR, OpenCV, and intelligent field extraction techniques to extract useful information from unstructured documents and return clean JSON output.

## ✨ Features

✅ Image & PDF text extraction  
✅ OCR powered document processing  
✅ Name, Email, Phone, Date & Amount extraction  
✅ GitHub, LinkedIn & Portfolio detection  
✅ Custom field extraction support  
✅ Image preprocessing for better accuracy  
✅ Noise removal and deskewing  
✅ REST API support  
✅ Docker deployment ready  

## 🛠️ Tech Stack

**Backend:** Python, Flask, REST API  
**OCR:** Tesseract OCR, OpenCV, Pillow  
**PDF Processing:** PyMuPDF, pdf2image  
**Extraction Engine:** Regex Patterns, Field Mapping, Validators  
**Deployment:** Docker, Render  

## ⚙️ How It Works

```
Upload Document
       ↓
Image/PDF Processing
       ↓
OCR Text Extraction
       ↓
Field Detection & Validation
       ↓
Structured JSON Response
```

## 📂 Project Structure

```
Document-Extractor
│
├── app.py
├── processor.py
├── parser.py
│
├── backend
│   ├── extractor.py
│   ├── field_mapper.py
│   ├── validators.py
│   ├── patterns.py
│   └── config.py
│
├── templates
├── static
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 API Usage

### Extract Document

Endpoint:

```
POST /extract
```

Upload image or PDF file and receive structured JSON response.

Example Response:

```json
{
  "status": "success",
  "data": {
    "email": "example@gmail.com",
    "phones": ["+91XXXXXXXXXX"],
    "dates": ["2025"]
  }
}
```

## 🚀 Deployment

The application is deployed using Docker on Render.

Live URL:

https://document-extractor-1-frq3.onrender.com

Deployment Stack:

- Docker Container
- Gunicorn WSGI Server
- Render Cloud Platform
## 🐳 Docker Support

```bash
docker build -t document-extractor .

docker run -p 5000:5000 document-extractor
```

## 🔮 Future Improvements

- AI/LLM based document understanding
- Document classification
- Cloud storage integration
- Advanced AI extraction pipeline

## 👨‍💻 Author

**Sagar Tripathi**

GitHub:
https://github.com/sagartripathi027

LinkedIn:
https://www.linkedin.com/in/sagartripathi027

⭐ If you like this project, give it a star!

Made with ❤️ using Python, Flask & OCR
