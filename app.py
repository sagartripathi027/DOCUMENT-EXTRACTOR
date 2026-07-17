import os
import logging
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from processor import extract_text
from parser import parse_structured_data, parse_requested_fields, get_supported_fields

# Initialize Flask app
app = Flask(__name__)

# CONFIGURATION
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_requested_fields_param():
    """
    Accepts requested fields from either:
      - form field 'fields' as a comma-separated and/or newline-separated
        string (e.g. from the <textarea name="fields"> in index.html)
          e.g. "Name, Email, GST" or "Name\nEmail\nGST"
      - repeated form/query fields 'fields'
          e.g. fields=Name&fields=Email
      - JSON body key 'fields' as a list (if request is JSON)
    Returns a list[str] (possibly empty) — empty means "no fields
    requested", which triggers the legacy full-extraction behavior.
    """
    import re

    def _split_field_string(raw):
        # Split on commas AND newlines/carriage returns in one pass
        return [f.strip() for f in re.split(r'[,\r\n]+', raw) if f.strip()]

    fields = []

    # multipart/form-data or x-www-form-urlencoded, repeated keys
    form_fields = request.form.getlist('fields')
    if form_fields:
        for item in form_fields:
            fields.extend(_split_field_string(item))

    # query string fallback (?fields=Name,Email)
    if not fields:
        query_fields = request.args.getlist('fields')
        for item in query_fields:
            fields.extend(_split_field_string(item))

    # JSON body fallback (if client sent application/json alongside file
    # is unusual for multipart, but support a pure-JSON 'fields' key
    # defensively in case someone sends fields via a JSON field).
    if not fields and request.is_json:
        try:
            body = request.get_json(silent=True) or {}
            json_fields = body.get('fields')
            if isinstance(json_fields, list):
                fields.extend([str(f).strip() for f in json_fields if str(f).strip()])
            elif isinstance(json_fields, str):
                fields.extend(_split_field_string(json_fields))
        except Exception:
            pass

    return fields


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fields', methods=['GET'])
def list_fields():
    """
    New introspection endpoint — lists all field names the engine
    natively understands (custom/unknown field names are still
    accepted at /extract via the generic fallback).
    """
    return jsonify({
        "status": "success",
        "supported_fields": get_supported_fields()
    })


@app.route('/extract', methods=['POST'])
def handle_extraction():

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PNG, JPG, JPEG, and PDF files are allowed"}), 400

    filepath = None  # safety

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        logger.info(f"Processing file: {filename}")

        # OCR (unchanged — processor.py is untouched)
        raw_text = extract_text(filepath)

        if not raw_text.strip():
            return jsonify({"error": "No text detected"}), 422

        # Determine whether the caller asked for specific fields.
        requested_fields = _parse_requested_fields_param()
        print("Requested Fields:", requested_fields)
        if requested_fields:
            # NEW universal path: extract only what was requested.
            structured_output = parse_requested_fields(raw_text, requested_fields)
        else:
            # LEGACY path: exact original behavior/response shape,
            # preserved for backward compatibility.
            structured_output = parse_structured_data(raw_text)

        # Cleanup
        os.remove(filepath)

        return jsonify({
            "status": "success",
            "data": structured_output
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}")

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)