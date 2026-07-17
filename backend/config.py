"""
backend/config.py

Centralized configuration for the extraction engine.

STRICT RULE: This module contains ONLY settings/constants — no
business logic, no extraction logic, no Flask routes. app.py reads
from here instead of hardcoding values inline.

.env loading is OPTIONAL: if python-dotenv isn't installed or no
.env file exists, sensible defaults are used and nothing breaks.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed — fall back to plain os.environ /
    # defaults below. Not a hard dependency for this project.
    pass


class Config:
    # ------------------------------------------------------------
    # Flask
    # ------------------------------------------------------------
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

    # ------------------------------------------------------------
    # Uploads
    # ------------------------------------------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

    # ------------------------------------------------------------
    # Extraction engine behavior
    # ------------------------------------------------------------
    # Max number of fields accepted in a single /extract request,
    # to prevent abuse via an unbounded 'fields' list.
    MAX_REQUESTED_FIELDS = int(os.getenv("MAX_REQUESTED_FIELDS", 50))

    # If True, unknown/custom field names fall back to generic
    # label-based extraction (extractor.extract_custom_field).
    # If False, unknown fields are silently dropped from the response.
    ALLOW_CUSTOM_FIELDS = os.getenv("ALLOW_CUSTOM_FIELDS", "true").lower() in ("1", "true", "yes")

    # ------------------------------------------------------------
    # Future AI/LLM-assisted extraction (requirement #9)
    #
    # Not wired up yet — reserved so that adding an LLM-backed
    # extraction fallback later requires NO changes to app.py's
    # public API, only a new extractor implementation gated behind
    # this flag inside extractor.py / parser.py.
    # ------------------------------------------------------------
    USE_LLM_FALLBACK = os.getenv("USE_LLM_FALLBACK", "false").lower() in ("1", "true", "yes")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "")   # e.g. "openai", "anthropic"
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")


def get_config():
    """Single accessor so callers don't import the class name directly."""
    return Config