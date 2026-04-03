# ============================================================
#  tests/test_ocr.py
#  Tests for the OCR text extraction service
#  Run: pytest tests/test_ocr.py -v
# ============================================================

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
from PIL import Image
from app.services.ocr_service import extract_text, _improve_image, _run_ocr


class TestImproveImage:
    """Test image preprocessing (before OCR)."""

    def test_returns_rgb(self):
        img = Image.new("RGB", (200, 100), "white")
        result = _improve_image(img)
        assert result.mode == "RGB"

    def test_handles_grayscale(self):
        img = Image.new("L", (200, 100), 128)
        result = _improve_image(img)
        assert result.mode == "RGB"

    def test_output_same_size(self):
        img = Image.new("RGB", (300, 150), "white")
        result = _improve_image(img)
        assert result.size == (300, 150)


class TestExtractText:
    """Test the main extract_text() function."""

    def test_raises_for_missing_file(self):
        with pytest.raises(ValueError, match="File not found"):
            extract_text("/tmp/this_file_does_not_exist.pdf")

    def test_extracts_from_image(self, tmp_path):
        # Create a simple white test image
        img = Image.new("RGB", (300, 100), "white")
        img_path = str(tmp_path / "test.png")
        img.save(img_path)

        # Mock OCR so we don't need real OCR installed in test
        with patch("app.services.ocr_service._run_ocr", return_value="Invoice No: 123"):
            result = extract_text(img_path)
            assert "Invoice No: 123" in result

    def test_returns_string(self, tmp_path):
        img = Image.new("RGB", (100, 50), "white")
        path = str(tmp_path / "blank.jpg")
        img.save(path)

        with patch("app.services.ocr_service._run_ocr", return_value=""):
            result = extract_text(path)
            assert isinstance(result, str)


class TestRunOcr:
    """Test the OCR function with fallback behaviour."""

    def test_fallback_to_tesseract_when_easyocr_fails(self):
        img = Image.new("RGB", (200, 80), "white")
        with patch("app.services.ocr_service._load_easyocr", side_effect=Exception("No model")):
            with patch("pytesseract.image_to_string", return_value="Fallback text"):
                result = _run_ocr(img)
                assert result == "Fallback text"

    def test_returns_empty_string_if_both_fail(self):
        img = Image.new("RGB", (100, 50), "white")
        with patch("app.services.ocr_service._load_easyocr", side_effect=Exception("fail")):
            with patch("pytesseract.image_to_string", side_effect=Exception("fail")):
                result = _run_ocr(img)
                assert result == ""
