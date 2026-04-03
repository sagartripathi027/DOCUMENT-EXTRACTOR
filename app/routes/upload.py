# ============================================================
#  routes/upload.py — Handle File Uploads
#
#  Endpoint: POST /upload
#  - Checks if file type is allowed
#  - Saves file with a unique name (UUID) to avoid conflicts
#  - Returns the file_id which is used for extraction
# ============================================================

import os
import uuid
from flask import Blueprint, request, jsonify, render_template, current_app

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/", methods=["GET"])
def index():
    """Show the main upload page."""
    return render_template("index.html")


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Accept a file upload from the frontend.

    Request: multipart/form-data with field "file"
    Response: JSON with file_id to use for extraction
    """

    # Check if file was included in request
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Please select a file."}), 400

    file = request.files["file"]

    # Check if user actually selected a file
    if not file or file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # Check if file type is allowed
    if not _is_allowed(file.filename):
        allowed = ", ".join(current_app.config["ALLOWED_EXTENSIONS"])
        return jsonify({"error": f"File type not allowed. Please upload: {allowed}"}), 400

    # Save file with UUID name to prevent conflicts
    # e.g. "invoice.pdf" → "a1b2c3d4.pdf"
    extension = file.filename.rsplit(".", 1)[-1].lower()
    file_id   = f"{uuid.uuid4().hex}.{extension}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_id)

    file.save(save_path)
    size_kb = round(os.path.getsize(save_path) / 1024, 1)

    print(f"File uploaded: {file.filename} → saved as {file_id} ({size_kb} KB)")

    return jsonify({
        "success":       True,
        "file_id":       file_id,
        "original_name": file.filename,
        "size_kb":       size_kb,
    }), 200


def _is_allowed(filename):
    """Check if the file extension is in our allowed list."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    from flask import current_app
    return ext in current_app.config["ALLOWED_EXTENSIONS"]
