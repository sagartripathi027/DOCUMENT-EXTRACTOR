import os
from flask import Flask
from backend.config import Config


def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Load all settings from Config class
    app.config.from_object(Config)

    # Create the data folders if they don't exist yet
    os.makedirs(app.config["UPLOAD_FOLDER"],    exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"],    exist_ok=True)
    os.makedirs(app.config["VECTOR_STORE_PATH"], exist_ok=True)

    # Register Blueprints (groups of routes)
    # Each blueprint handles a specific part of the app
    from backend.routes.upload    import upload_bp
    from backend.routes.extract   import extract_bp
    from backend.routes.dashboard import dashboard_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(extract_bp)
    app.register_blueprint(dashboard_bp)

    # Handle 404 errors nicely
    @app.errorhandler(404)
    def not_found(e):
        from flask import jsonify
        return jsonify({"error": "Page not found"}), 404

    # Handle file too large error
    @app.errorhandler(413)
    def too_large(e):
        from flask import jsonify
        return jsonify({"error": "File is too large. Maximum size is 16MB."}), 413

    return app
