# ============================================================
#  run.py — Start the Flask web application
#  Usage: python run.py
# ============================================================

from app import create_app

# Create the Flask app using our factory function
app = create_app()

if __name__ == "__main__":
    print("Starting DocExtractor...")
    print("Open your browser at: http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
