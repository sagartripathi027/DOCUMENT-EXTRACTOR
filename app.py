import os
import logging
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from processor import extract_text
from parser import parse_structured_data

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

@app.route('/')
def index():
    return render_template('index.html')

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

        # OCR
        raw_text = extract_text(filepath)

        if not raw_text.strip():
            return jsonify({"error": "No text detected"}), 422

        # Parsing
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
