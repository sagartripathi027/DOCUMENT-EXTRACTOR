# DocExtractor — AI Document to Excel Pipeline
### Final Year / Mini College Project

> Upload an invoice, receipt or bank statement → AI extracts all data → Download as Excel

---

## What This Project Does

This project uses a **5-step AI pipeline** to convert unstructured documents (images/PDFs) into structured Excel files:

```
Image/PDF → OCR → ML Classify → NER Extract → GPT Correct → Excel
```

| Step | Technology | What it does |
|------|-----------|-------------|
| 1. OCR | EasyOCR + Tesseract | Reads text from image/PDF |
| 2. Classify | scikit-learn (TF-IDF + LR) | Detects invoice/receipt/bank statement |
| 3. NER Extract | Regex + HuggingFace BERT | Pulls out dates, amounts, names |
| 4. GPT Correct | OpenAI GPT-4o-mini + FAISS RAG | Fixes errors, normalizes data |
| 5. Excel Export | pandas + openpyxl | Creates formatted .xlsx file |

---

## Tech Stack

- **Backend**: Flask (Python)
- **OCR**: EasyOCR, Tesseract, PyMuPDF
- **ML**: scikit-learn (TF-IDF + Logistic Regression)
- **NLP/NER**: HuggingFace Transformers (BERT)
- **LLM**: OpenAI GPT-4o-mini
- **RAG**: FAISS + Sentence Transformers
- **Export**: pandas, openpyxl
- **Frontend**: HTML, CSS, JavaScript (no framework needed)

---

## Project Structure

```
college_project/
├── app/
│   ├── __init__.py          ← Flask app factory
│   ├── config.py            ← All settings
│   ├── routes/
│   │   ├── upload.py        ← POST /upload
│   │   ├── extract.py       ← POST /extract (main pipeline)
│   │   └── dashboard.py     ← GET /dashboard + /download
│   ├── services/
│   │   ├── ocr_service.py   ← Text extraction
│   │   ├── classifier.py    ← ML document classifier
│   │   ├── ner_extractor.py ← Field extraction
│   │   ├── llm_service.py   ← GPT correction + RAG
│   │   └── excel_exporter.py← Excel generation
│   ├── models/
│   │   └── loader.py        ← Shared model cache
│   ├── templates/           ← HTML pages
│   └── static/              ← CSS and JS
├── data/
│   ├── uploads/             ← Uploaded files
│   ├── outputs/             ← Generated Excel files
│   └── vector_store/        ← FAISS RAG index
├── tests/                   ← Unit + integration tests
├── train_classifier.py      ← Train ML model (run once)
├── run.py                   ← Start the app
└── requirements.txt
```

---

## How to Run (Windows)

```powershell
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Download spaCy model (optional, for better NER)
python -m spacy download en_core_web_sm

# 4. Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# During install, select "Add to PATH"

# 5. Set your OpenAI API key
# Open .env file and replace: OPENAI_API_KEY=your-openai-api-key-here

# 6. Train the ML classifier (only needs to be done once)
python train_classifier.py

# 7. Start the app
python run.py
# Open: http://localhost:5000
```

## How to Run (Linux / Mac)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo apt-get install tesseract-ocr    # Ubuntu
# brew install tesseract              # Mac
python train_classifier.py
python run.py
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Upload page |
| POST | `/upload` | Upload file, get file_id |
| POST | `/extract` | Run AI pipeline on file |
| POST | `/extract/batch` | Process multiple files |
| GET | `/dashboard` | View all output files |
| GET | `/download/<file>` | Download Excel file |
| GET | `/api/health` | Health check |

---

## Project by
**Sagar Tripathi**
College Project — AI/ML Document Extraction System
