# ============================================================
#  tests/test_ner.py
#  Tests for the NER field extractor
#  Run: pytest tests/test_ner.py -v
# ============================================================

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.services.ner_extractor import (
    _extract_with_regex,
    _find_date,
    _find_amount,
    _to_float,
)


class TestToFloat:
    """Test the helper that cleans currency strings to numbers."""

    def test_rupee(self):        assert _to_float("₹5,000.50")  == 5000.5
    def test_dollar(self):       assert _to_float("$1,234")      == 1234.0
    def test_plain(self):        assert _to_float("9999.99")     == 9999.99
    def test_commas(self):       assert _to_float("10,00,000")   == 1000000.0
    def test_bad_input(self):    assert _to_float("bad input")   == 0.0
    def test_none(self):         assert _to_float(None)          == 0.0


class TestFindDate:
    """Test date detection using regex."""

    def test_dd_mm_yyyy(self):
        assert _find_date("Date: 12/03/2024") == "12/03/2024"

    def test_yyyy_mm_dd(self):
        assert _find_date("2024-03-12") == "2024-03-12"

    def test_no_date(self):
        assert _find_date("no date in this text") is None

    def test_date_in_sentence(self):
        result = _find_date("Invoice issued on 05/01/2024 for services")
        assert result == "05/01/2024"


class TestFindAmount:
    """Test amount/currency detection."""

    def test_total_label(self):
        assert _find_amount("Total Amount: ₹5,000") == 5000.0

    def test_grand_total(self):
        result = _find_amount("Grand Total: $1,234.56")
        assert result is not None

    def test_currency_symbol(self):
        assert _find_amount("Pay ₹999 now") == 999.0

    def test_no_amount(self):
        assert _find_amount("no numbers here") is None


class TestRegexExtract:
    """Test regex-based field extraction for different document types."""

    # ── Invoice fields ──────────────────────────────────────────────────────
    def test_invoice_no(self):
        f = _extract_with_regex("Invoice No: INV-2024-001 Amount: ₹5000", "invoice")
        assert f.get("invoice_no") == "INV-2024-001"

    def test_due_date(self):
        f = _extract_with_regex("Due Date: 31/03/2024", "invoice")
        assert f.get("due_date") == "31/03/2024"

    def test_gst_amount(self):
        f = _extract_with_regex("GST: ₹450", "invoice")
        assert "tax_amount" in f
        assert f["tax_amount"] == 450.0

    def test_gstin(self):
        f = _extract_with_regex("GSTIN: 27AABCU9603R1ZX", "invoice")
        assert f.get("gstin") == "27AABCU9603R1ZX"

    # ── Receipt fields ──────────────────────────────────────────────────────
    def test_receipt_no(self):
        f = _extract_with_regex("Receipt No: REC-456", "receipt")
        assert f.get("receipt_no") == "REC-456"

    def test_payment_mode_cash(self):
        f = _extract_with_regex("Payment Mode: CASH Total: 500", "receipt")
        assert f.get("payment_mode") == "CASH"

    def test_payment_mode_upi(self):
        f = _extract_with_regex("Paid by: UPI Transaction 12345", "receipt")
        assert f.get("payment_mode") == "UPI"

    # ── Bank statement fields ───────────────────────────────────────────────
    def test_closing_balance(self):
        f = _extract_with_regex("Closing Balance: ₹45,000.00", "bank_statement")
        assert f.get("closing_balance") == 45000.0

    def test_opening_balance(self):
        f = _extract_with_regex("Opening Balance: ₹50,000", "bank_statement")
        assert f.get("opening_balance") == 50000.0

    def test_date_found_in_all_types(self):
        text = "Date: 15/08/2024 Amount: ₹1000"
        for doc_type in ["invoice", "receipt", "bank_statement"]:
            f = _extract_with_regex(text, doc_type)
            assert "date" in f
