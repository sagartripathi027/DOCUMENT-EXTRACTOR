# ============================================================
#  models/loader.py — Load ML Models Once, Reuse Every Time
#
#  Problem: Loading ML models on every request is very slow.
#  Solution: Load them once and keep them in memory (_cache).
#
#  This is called "model caching" — an important optimization!
# ============================================================

import os
import logging

logger  = logging.getLogger(__name__)
_cache  = {}   # Dictionary to hold all loaded models in memory


def get_classifier(model_path):
    """
    Load the trained document classifier.
    Returns None if model file doesn't exist yet (uses keyword fallback).
    """
    if "classifier" in _cache:
        return _cache["classifier"]   # Already loaded, return from memory

    if not os.path.exists(model_path):
        logger.warning(f"Classifier model not found at '{model_path}'")
        logger.warning("Run 'python train_classifier.py' to train it.")
        _cache["classifier"] = None
        return None

    try:
        import pickle
        with open(model_path, "rb") as f:
            _cache["classifier"] = pickle.load(f)
        logger.info(f"Classifier loaded from {model_path}")
    except Exception as e:
        logger.error(f"Failed to load classifier: {e}")
        _cache["classifier"] = None

    return _cache["classifier"]


def get_ner_pipeline(model_name):
    """
    Load the HuggingFace NER pipeline.
    dslim/bert-base-NER is a BERT model fine-tuned for Named Entity Recognition.
    """
    if "ner" in _cache:
        return _cache["ner"]

    try:
        from transformers import pipeline
        logger.info(f"Loading NER model: {model_name} ...")
        _cache["ner"] = pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",
            device=-1   # -1 means CPU (no GPU needed)
        )
        logger.info("NER model loaded!")
    except Exception as e:
        logger.error(f"NER model load failed: {e}")
        _cache["ner"] = None

    return _cache["ner"]


def get_sentence_embedder(model_name="all-MiniLM-L6-v2"):
    """
    Load the sentence transformer for RAG embeddings.
    all-MiniLM-L6-v2 converts sentences to 384-dim vectors.
    """
    if "embedder" in _cache:
        return _cache["embedder"]

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence embedder...")
        _cache["embedder"] = SentenceTransformer(model_name)
        logger.info("Embedder loaded!")
    except Exception as e:
        logger.error(f"Embedder load failed: {e}")
        _cache["embedder"] = None

    return _cache["embedder"]
