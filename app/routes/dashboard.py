# ============================================================
#  routes/dashboard.py — Show Results and Download Files
#
#  Endpoints:
#    GET /dashboard        → HTML page listing all output files
#    GET /download/<file>  → Download a specific Excel file
#    GET /api/files        → JSON list of all output files
#    GET /api/health       → Health check (for deployment)
# ============================================================

import os
from flask import Blueprint, render_template, send_from_directory, jsonify, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    """Show the dashboard page with all generated Excel files."""
    output_folder = current_app.config["OUTPUT_FOLDER"]
    files = []

    if os.path.exists(output_folder):
        # Get all Excel files, newest first
        for filename in sorted(os.listdir(output_folder), reverse=True):
            if filename.endswith(".xlsx"):
                filepath = os.path.join(output_folder, filename)
                files.append({
                    "name":    filename,
                    "size_kb": round(os.path.getsize(filepath) / 1024, 1),
                    "url":     f"/download/{filename}",
                })

    return render_template("dashboard.html", files=files)


@dashboard_bp.route("/download/<filename>")
def download_file(filename):
    """Download a specific Excel file."""
    # Security check: only allow .xlsx files
    if not filename.endswith(".xlsx"):
        return jsonify({"error": "Only Excel files can be downloaded."}), 400

    output_folder = os.path.abspath(current_app.config["OUTPUT_FOLDER"])
    return send_from_directory(output_folder, filename, as_attachment=True)


@dashboard_bp.route("/api/files")
def list_files():
    """Return a JSON list of all output files (used by frontend JS)."""
    output_folder = current_app.config["OUTPUT_FOLDER"]
    files = []

    if os.path.exists(output_folder):
        for filename in sorted(os.listdir(output_folder), reverse=True):
            if filename.endswith(".xlsx"):
                filepath = os.path.join(output_folder, filename)
                files.append({
                    "filename": filename,
                    "size_kb":  round(os.path.getsize(filepath) / 1024, 1),
                    "url":      f"/download/{filename}",
                })

    return jsonify({"files": files, "total": len(files)})


@dashboard_bp.route("/api/health")
def health_check():
    """
    Simple health check endpoint.
    Used by deployment platforms to check if app is running.
    Returns 200 OK if everything is fine.
    """
    return jsonify({
        "status":  "running",
        "project": "DocExtractor — College Project",
        "author":  "Sagar Tripathi"
    }), 200
