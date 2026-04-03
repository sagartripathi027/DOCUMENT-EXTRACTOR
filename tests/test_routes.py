# ============================================================
#  tests/test_routes.py
#  Integration tests for all Flask API endpoints
#  Run: pytest tests/test_routes.py -v
# ============================================================

import os, sys, io, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
from PIL import Image

# Set test environment before importing app
os.environ["FLASK_ENV"]        = "development"
os.environ["FLASK_SECRET_KEY"] = "test-secret"
os.environ["OPENAI_API_KEY"]   = "test-key"

from app import create_app
from app.config import Config


# ── Test Config ───────────────────────────────────────────────────────────────

class TestConfig(Config):
    TESTING              = True
    UPLOAD_FOLDER        = "data/test_uploads"
    OUTPUT_FOLDER        = "data/test_outputs"
    VECTOR_STORE_PATH    = "data/test_vectors"


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config.from_object(TestConfig)
    yield application


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def setup_dirs(app):
    """Create test directories before each test."""
    for folder in ["UPLOAD_FOLDER", "OUTPUT_FOLDER", "VECTOR_STORE_PATH"]:
        os.makedirs(app.config[folder], exist_ok=True)
    yield
    # Cleanup: remove test files after each test
    for folder in ["UPLOAD_FOLDER", "OUTPUT_FOLDER"]:
        path = app.config[folder]
        if os.path.exists(path):
            for f in os.listdir(path):
                try: os.remove(os.path.join(path, f))
                except: pass


# ── Health Check ──────────────────────────────────────────────────────────────

class TestHealthCheck:

    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_returns_running(self, client):
        data = json.loads(client.get("/api/health").data)
        assert data["status"] == "running"


# ── Page Routes ───────────────────────────────────────────────────────────────

class TestPages:

    def test_home_page_loads(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"DocExtractor" in r.data

    def test_dashboard_loads(self, client):
        r = client.get("/dashboard")
        assert r.status_code == 200
        assert b"Dashboard" in r.data


# ── Upload Endpoint ───────────────────────────────────────────────────────────

class TestUpload:

    def test_no_file_gives_400(self, client):
        r = client.post("/upload")
        assert r.status_code == 400

    def test_wrong_file_type_gives_400(self, client):
        data = {"file": (io.BytesIO(b"data"), "virus.exe")}
        r = client.post("/upload", data=data, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_valid_pdf_upload(self, client):
        data = {"file": (io.BytesIO(b"%PDF-1.4 fake content"), "invoice.pdf")}
        r    = client.post("/upload", data=data, content_type="multipart/form-data")
        assert r.status_code == 200

        body = json.loads(r.data)
        assert "file_id" in body
        assert body["file_id"].endswith(".pdf")
        assert body["original_name"] == "invoice.pdf"

    def test_valid_image_upload(self, client):
        # Create a real PNG in memory
        buf = io.BytesIO()
        Image.new("RGB", (100, 50), "white").save(buf, format="PNG")
        buf.seek(0)

        data = {"file": (buf, "receipt.png")}
        r    = client.post("/upload", data=data, content_type="multipart/form-data")
        assert r.status_code == 200

    def test_uploaded_file_is_saved(self, client, app):
        data = {"file": (io.BytesIO(b"test content"), "test.pdf")}
        r    = client.post("/upload", data=data, content_type="multipart/form-data")
        body = json.loads(r.data)

        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], body["file_id"])
        assert os.path.exists(saved_path)


# ── Extract Endpoint ──────────────────────────────────────────────────────────

class TestExtract:

    def test_missing_file_id_gives_400(self, client):
        r = client.post("/extract", json={})
        assert r.status_code == 400

    def test_nonexistent_file_gives_404(self, client):
        r = client.post("/extract", json={"file_id": "doesnotexist.pdf"})
        assert r.status_code == 404

    def test_empty_ocr_gives_422(self, client, app):
        # Upload an image
        buf = io.BytesIO()
        Image.new("RGB", (50, 50), "white").save(buf, format="PNG")
        buf.seek(0)
        up   = client.post("/upload", data={"file": (buf, "blank.png")},
                           content_type="multipart/form-data")
        fid  = json.loads(up.data)["file_id"]

        # Mock OCR to return empty string
        with patch("app.services.ocr_service.extract_text", return_value="   "):
            r = client.post("/extract", json={"file_id": fid})
        assert r.status_code == 422

    def test_full_pipeline_success(self, client, app):
        # Upload a test image
        buf = io.BytesIO()
        Image.new("RGB", (300, 100), "white").save(buf, format="PNG")
        buf.seek(0)
        up  = client.post("/upload", data={"file": (buf, "invoice.png")},
                          content_type="multipart/form-data")
        fid = json.loads(up.data)["file_id"]

        # Mock all heavy services so test runs fast
        mock_fields = {"invoice_no": "INV-001", "amount": 5000.0,
                       "date": "2024-03-12", "doc_type": "invoice"}

        with patch("app.services.ocr_service.extract_text",
                   return_value="Invoice No: INV-001 Amount ₹5000"):
            with patch("app.services.classifier.classify_document",
                       return_value="invoice"):
                with patch("app.services.ner_extractor.extract_fields",
                           return_value=mock_fields):
                    with patch("app.services.llm_service.correct_and_normalize",
                               return_value=mock_fields):
                        with patch("app.services.llm_service.save_to_vector_store"):
                            r = client.post("/extract", json={"file_id": fid})

        assert r.status_code == 200
        body = json.loads(r.data)
        assert body["status"]   == "success"
        assert body["doc_type"] == "invoice"
        assert "fields"     in body
        assert "excel_url"  in body


# ── Dashboard Endpoints ───────────────────────────────────────────────────────

class TestDashboard:

    def test_api_files_returns_json(self, client):
        r    = client.get("/api/files")
        body = json.loads(r.data)
        assert r.status_code == 200
        assert "files" in body
        assert isinstance(body["files"], list)

    def test_download_wrong_extension_blocked(self, client):
        r = client.get("/download/malware.exe")
        assert r.status_code == 400

    def test_download_missing_file_404(self, client):
        r = client.get("/download/nonexistent.xlsx")
        assert r.status_code == 404
