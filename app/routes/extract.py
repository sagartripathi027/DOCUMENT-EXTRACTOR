# ============================================================
#  routes/extract.py — Run the Full AI Pipeline
#
#  This is the heart of the project!
#  It chains all 5 AI steps together:
#
#  Step 1: OCR          → Get text from image/PDF
#  Step 2: Classify     → What type of document is this?
#  Step 3: NER Extract  → Pull out fields (date, amount, etc.)
#  Step 4: LLM Correct  → GPT fixes and normalizes the data
#  Step 5: Export       → Save to Excel file
#
#  Endpoints:
#    POST /extract       → Single file
#    POST /extract/batch → Multiple files at once
# ============================================================

import os
from flask import Blueprint, request, jsonify, current_app

# Import all our AI service modules
from app.services import ocr_service
from app.services import classifier
from app.services import ner_extractor
from app.services import llm_service
from app.services import excel_exporter

extract_bp = Blueprint("extract", __name__)


def _run_full_pipeline(file_id, config):
    """
    Run the complete 5-step AI pipeline on a single file.

    Returns a dict with:
      - raw_text: what OCR extracted
      - doc_type: invoice / receipt / bank_statement
      - fields:   the final extracted + corrected data
    """

    # ── Step 1: Load the file ─────────────────────────────────────────────────
    file_path = os.path.join(config["UPLOAD_FOLDER"], file_id)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_id}' not found. Please upload it first.")

    print(f"\n{'='*50}")
    print(f"Processing: {file_id}")
    print(f"{'='*50}")

    # ── Step 2: OCR — Extract text ────────────────────────────────────────────
    print("Step 1/5: Running OCR...")
    raw_text = ocr_service.extract_text(file_path)

    if not raw_text.strip():
        raise ValueError("Could not extract any text. Please check the file quality.")

    print(f"  Extracted {len(raw_text)} characters")

    # ── Step 3: Classify document type ───────────────────────────────────────
    print("Step 2/5: Classifying document type...")
    doc_type = classifier.classify_document(
        raw_text,
        model_path=config["CLASSIFIER_MODEL_PATH"]
    )
    print(f"  Document type: {doc_type}")

    # ── Step 4: NER — Extract key fields ─────────────────────────────────────
    print("Step 3/5: Extracting fields with NER...")
    fields = ner_extractor.extract_fields(
        text=raw_text,
        doc_type=doc_type,
        model_name=config["NER_MODEL_NAME"]
    )
    fields["doc_type"]    = doc_type
    fields["source_file"] = file_id
    print(f"  Found fields: {list(fields.keys())}")

    # ── Step 5: LLM — Correct and normalize with GPT ─────────────────────────
    print("Step 4/5: Correcting with GPT + RAG...")
    corrected_fields = llm_service.correct_and_normalize(
        raw_text=raw_text,
        doc_type=doc_type,
        extracted_fields=fields,
        store_path=config["VECTOR_STORE_PATH"]
    )

    # Save to vector store for future RAG lookups
    llm_service.save_to_vector_store(
        doc_text=raw_text,
        fields=corrected_fields,
        store_path=config["VECTOR_STORE_PATH"]
    )

    print("Step 5/5: Done!")

    return {
        "raw_text": raw_text,
        "doc_type": doc_type,
        "fields":   corrected_fields,
    }


@extract_bp.route("/extract", methods=["POST"])
def extract():
    """
    Run extraction pipeline on a single uploaded file.

    Request body (JSON):
      { "file_id": "abc123.pdf" }

    Response:
      {
        "status": "success",
        "doc_type": "invoice",
        "fields": { "date": "2024-03-12", "amount": 5000.0, ... },
        "excel_url": "/download/extracted_20240312_123456.xlsx"
      }
    """
    body    = request.get_json(silent=True) or {}
    file_id = body.get("file_id") or request.form.get("file_id")

    if not file_id:
        return jsonify({"error": "Please provide a file_id in the request body."}), 400

    # Pass config as dict to avoid Flask context issues in helper function
    config = {
        "UPLOAD_FOLDER":         current_app.config["UPLOAD_FOLDER"],
        "OUTPUT_FOLDER":         current_app.config["OUTPUT_FOLDER"],
        "VECTOR_STORE_PATH":     current_app.config["VECTOR_STORE_PATH"],
        "CLASSIFIER_MODEL_PATH": current_app.config["CLASSIFIER_MODEL_PATH"],
        "NER_MODEL_NAME":        current_app.config["NER_MODEL_NAME"],
    }

    try:
        result = _run_full_pipeline(file_id, config)

        # Export to Excel
        excel_path = excel_exporter.export_to_excel(
            records=[result["fields"]],
            output_folder=config["OUTPUT_FOLDER"]
        )
        excel_filename = os.path.basename(excel_path)

        return jsonify({
            "status":           "success",
            "doc_type":         result["doc_type"],
            "fields":           result["fields"],
            "raw_text_preview": result["raw_text"][:300],  # First 300 chars as preview
            "excel_url":        f"/download/{excel_filename}",
        }), 200

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except Exception as e:
        print(f"Extraction error: {e}")
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


@extract_bp.route("/extract/batch", methods=["POST"])
def extract_batch():
    """
    Process multiple files at once and combine into one Excel.

    Request body:
      { "file_ids": ["abc.pdf", "xyz.jpg", "doc.png"] }
    """
    body     = request.get_json(silent=True) or {}
    file_ids = body.get("file_ids", [])

    if not file_ids:
        return jsonify({"error": "Please provide a list of file_ids."}), 400

    config = {
        "UPLOAD_FOLDER":         current_app.config["UPLOAD_FOLDER"],
        "OUTPUT_FOLDER":         current_app.config["OUTPUT_FOLDER"],
        "VECTOR_STORE_PATH":     current_app.config["VECTOR_STORE_PATH"],
        "CLASSIFIER_MODEL_PATH": current_app.config["CLASSIFIER_MODEL_PATH"],
        "NER_MODEL_NAME":        current_app.config["NER_MODEL_NAME"],
    }

    all_records = []
    errors      = []

    for file_id in file_ids:
        try:
            result = _run_full_pipeline(file_id, config)
            all_records.append(result["fields"])
        except Exception as e:
            print(f"Failed to process {file_id}: {e}")
            errors.append({"file_id": file_id, "error": str(e)})

    if not all_records:
        return jsonify({"error": "None of the files could be processed.", "details": errors}), 422

    # Export all records to one Excel file
    excel_path     = excel_exporter.export_to_excel(all_records, config["OUTPUT_FOLDER"])
    excel_filename = os.path.basename(excel_path)

    return jsonify({
        "status":    "success",
        "processed": len(all_records),
        "failed":    len(errors),
        "errors":    errors,
        "excel_url": f"/download/{excel_filename}",
    }), 200
