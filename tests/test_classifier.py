# ============================================================
#  tests/test_classifier.py
#  Tests for the ML document classifier
#  Run: pytest tests/test_classifier.py -v
# ============================================================

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.services.classifier import (
    classify_document,
    _classify_with_keywords,
    train_and_save_model,
)


class TestKeywordClassifier:
    """Test the keyword-based fallback classifier."""

    def test_detects_invoice(self):
        text = "Invoice No: INV-001 Bill To: ABC Ltd GST 500 Due Date 12/03/2024"
        assert _classify_with_keywords(text) == "invoice"

    def test_detects_receipt(self):
        text = "Receipt Thank you for your purchase Total Paid $50 Cashier John"
        assert _classify_with_keywords(text) == "receipt"

    def test_detects_bank_statement(self):
        text = "Bank Statement Account Number 12345 Opening Balance 10000 Debit Credit"
        assert _classify_with_keywords(text) == "bank_statement"

    def test_returns_unknown_for_random_text(self):
        assert _classify_with_keywords("hello world random words nothing relevant") == "unknown"

    def test_case_insensitive(self):
        text = "INVOICE NO: 123 BILL TO: ABC COMPANY DUE DATE: 12/03/2024 GST VENDOR"
        assert _classify_with_keywords(text) == "invoice"


class TestFullClassifier:
    """Test classify_document() — uses ML model if available, else keywords."""

    def test_returns_valid_label(self):
        text = "Invoice No: 123 Bill To: ABC Amount 5000"
        result = classify_document(text, model_path="nonexistent.pkl")
        assert result in ["invoice", "receipt", "bank_statement", "unknown"]

    def test_invoice_text(self):
        text = "Invoice No: INV-2024 Bill To: XYZ Ltd Amount Due 12000 GST 2160"
        result = classify_document(text, model_path="nonexistent.pkl")
        assert result == "invoice"


class TestTrainAndSave:
    """Test that we can train and save the classifier."""

    def test_trains_and_saves_model(self, tmp_path):
        texts = [
            "Invoice No Bill To GST Amount Due Vendor",
            "Invoice Number Tax Invoice GST Net Payable",
            "Receipt Total Paid Cashier Store Payment",
            "Receipt Thank you purchase Cash Total",
            "Bank Statement Account Balance Debit Credit",
            "Bank Statement Opening Closing Balance NEFT",
        ]
        labels = ["invoice", "invoice", "receipt", "receipt", "bank_statement", "bank_statement"]

        save_path = str(tmp_path / "test_model.pkl")
        model = train_and_save_model(texts, labels, save_path=save_path)

        # Model file should exist
        assert os.path.exists(save_path)

        # Model should be able to make predictions
        pred = model.predict(["Invoice No: 999 Bill To: Someone"])[0]
        assert pred in ["invoice", "receipt", "bank_statement"]
