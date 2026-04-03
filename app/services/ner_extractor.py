# ============================================================
#  ner_extractor.py — Pull Out Key Information from Text
#
#  NER = Named Entity Recognition
#  It finds specific pieces of information like:
#    - Invoice numbers, dates, amounts
#    - Vendor names, person names
#
#  Two approaches used:
#    1. Regex  — pattern matching (fast, works for dates/numbers)
#    2. AI NER — HuggingFace BERT model (finds names & organizations)
# ============================================================

import re

# HuggingFace NER model — loaded once, reused every time
_ner_model = None


def _load_ner_model(model_name):
    """Load NER model into memory (heavy, so we do it once)."""
    global _ner_model
    if _ner_model is None:
        from transformers import pipeline
        print(f"Loading NER model: {model_name}")
        _ner_model = pipeline("ner", model=model_name,
                               aggregation_strategy="simple", device=-1)
        print("NER model ready!")
    return _ner_model


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def extract_fields(text, doc_type, model_name="dslim/bert-base-NER"):
    """
    Extract all key fields from the document text.

    Steps:
    1. Use regex to find dates, amounts, IDs
    2. Use AI NER to find vendor names, person names
    3. Combine both results

    Returns: A dictionary like:
      {
        "date": "12/03/2024",
        "amount": 5000.0,
        "invoice_no": "INV-001",
        "vendor": "ABC Pvt Ltd"
      }
    """
    # Step 1: Extract using regex patterns
    fields = _extract_with_regex(text, doc_type)

    # Step 2: Extract names using AI NER
    ai_entities = _extract_with_ner(text, model_name)

    # Step 3: Merge (regex takes priority over AI if conflict)
    combined = {**ai_entities, **fields}
    return combined


# ── REGEX EXTRACTION ──────────────────────────────────────────────────────────

def _extract_with_regex(text, doc_type):
    """Use regular expressions to find structured data like dates and amounts."""
    fields = {}

    # --- Find Date ---
    # Matches formats: 12/03/2024 or 2024-03-12 or 12 March 2024
    date_match = re.search(
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})\b",
        text
    )
    if date_match:
        fields["date"] = date_match.group(1)

    # --- Find Amount ---
    # First look for labelled amounts: "Total: ₹5000" or "Amount: $1234"
    amount_match = re.search(
        r"(?:total|amount|grand total|net payable|amount due)[^\d\n]{0,20}([\$₹£€]?\s?[\d,]+\.?\d*)",
        text, re.IGNORECASE
    )
    if amount_match:
        fields["amount"] = _to_float(amount_match.group(1))
    else:
        # Fallback: find any currency amount
        any_amount = re.search(r"([\$₹£€]\s?[\d,]+\.?\d*)", text)
        if any_amount:
            fields["amount"] = _to_float(any_amount.group(1))

    # --- Invoice specific fields ---
    if doc_type == "invoice":
        # Invoice number
        inv = re.search(r"invoice\s*(?:no|number|#)[:\s#]*([A-Z0-9\/\-]+)", text, re.IGNORECASE)
        if inv:
            fields["invoice_no"] = inv.group(1).strip()

        # Due date
        due = re.search(r"due\s*date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})", text, re.IGNORECASE)
        if due:
            fields["due_date"] = due.group(1)

        # GST / Tax amount
        gst = re.search(r"(?:gst|tax|vat)[^\d\n]{0,15}([\d,]+\.?\d*)", text, re.IGNORECASE)
        if gst:
            fields["tax_amount"] = _to_float(gst.group(1))

        # GSTIN number
        gstin = re.search(r"gstin[:\s]*([A-Z0-9]{15})", text, re.IGNORECASE)
        if gstin:
            fields["gstin"] = gstin.group(1).upper()

    # --- Receipt specific fields ---
    elif doc_type == "receipt":
        # Receipt number
        rec = re.search(r"receipt\s*(?:no|#)[:\s#]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        if rec:
            fields["receipt_no"] = rec.group(1).strip()

        # Payment mode (Cash / Card / UPI)
        pay = re.search(r"(?:paid by|payment mode|payment type)[:\s]*(cash|card|upi|online)", text, re.IGNORECASE)
        if pay:
            fields["payment_mode"] = pay.group(1).upper()

    # --- Bank Statement specific fields ---
    elif doc_type == "bank_statement":
        # Account number
        acc = re.search(r"account\s*(?:no|number)[:\s]*([\dXx\*\s]{8,20})", text, re.IGNORECASE)
        if acc:
            fields["account_no"] = acc.group(1).strip()

        # Closing balance
        closing = re.search(r"closing\s*balance[:\s]*([\$₹£€]?\s?[\d,]+\.?\d*)", text, re.IGNORECASE)
        if closing:
            fields["closing_balance"] = _to_float(closing.group(1))

        # Opening balance
        opening = re.search(r"opening\s*balance[:\s]*([\$₹£€]?\s?[\d,]+\.?\d*)", text, re.IGNORECASE)
        if opening:
            fields["opening_balance"] = _to_float(opening.group(1))

    return fields


# ── AI NER EXTRACTION ─────────────────────────────────────────────────────────

def _extract_with_ner(text, model_name):
    """
    Use BERT-based NER to find:
    - ORG → organization / vendor name
    - PER → person name
    - LOC → location
    """
    entities = {}
    try:
        ner = _load_ner_model(model_name)

        # Only send first 512 characters (BERT token limit)
        results = ner(text[:512])

        for entity in results:
            label      = entity.get("entity_group", "")
            word       = entity.get("word", "").strip()
            confidence = entity.get("score", 0)

            # Only use high-confidence predictions
            if confidence < 0.80 or not word:
                continue

            if label == "ORG" and "vendor"   not in entities:
                entities["vendor"]   = word
            if label == "PER" and "person"   not in entities:
                entities["person"]   = word
            if label == "LOC" and "location" not in entities:
                entities["location"] = word

    except Exception as e:
        print(f"NER extraction failed: {e}")

    return entities


# ── HELPER ────────────────────────────────────────────────────────────────────

def _to_float(raw_string):
    """
    Convert a messy string to a clean float number.
    Examples:
      "₹5,000.50"  →  5000.5
      "$1,234"     →  1234.0
      "bad text"   →  0.0
    """
    try:
        # Remove everything except digits and decimal point
        cleaned = re.sub(r"[^\d\.]", "", str(raw_string))
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0
