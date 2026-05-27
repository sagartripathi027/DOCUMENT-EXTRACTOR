#  config.py — App settings loaded from .env file

import os
from dotenv import load_dotenv

# Load the .env file so we can use os.getenv()
load_dotenv()

class Config:
    # Flask needs a secret key for session security
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "college-project-secret")

    # Where to save uploaded files
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "data/uploads")

    # Where to save generated Excel files
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "data/outputs")

    # Where to store the RAG vector database
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "data/vector_store")

    # Max file upload size = 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Only these file types are allowed
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "tiff"}

    # Your OpenAI API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Path to our trained ML model file
    CLASSIFIER_MODEL_PATH = "app/models/classifier_model.pkl"

    # HuggingFace NER model for extracting names/vendors
    NER_MODEL_NAME = "dslim/bert-base-NER"
