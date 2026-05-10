# ============================================================
#  classifier.py — Identify What Type of Document It Is
#
#  This is our ML (Machine Learning) module!
#  It figures out if a document is:
#    - Invoice
#    - Receipt
#    - Bank Statement
#    - Unknown
#
#  How it works:
#    1. If we have a trained model → use ML prediction
#    2. Otherwise → count keywords (smart keyword matching)
#
#  The ML model is trained in: train_classifier.py
# ============================================================

import os
import re
import pickle

# Keywords that appear in each document type
# The more keywords found, the more confident we are
DOCUMENT_KEYWORDS = {
    "invoice": [
        "invoice", "invoice no", "invoice number",
        "bill to", "ship to", "due date",
        "gst", "gstin", "vendor", "purchase order",
        "net payable", "tax invoice", "amount due",
    ],
    "receipt": [
        "receipt", "thank you for your purchase",
        "total paid", "cashier", "payment received",
        "sales receipt", "cash", "card payment", "paid",
    ],
    "bank_statement": [
        "statement", "account number", "account no",
        "balance", "debit", "credit", "opening balance",
        "closing balance", "neft", "imps", "upi",
        "withdrawal", "deposit", "transaction",
    ],
}

# This will hold our trained ML model in memory
_trained_model = None


def _load_model(model_path):
    """Load the trained ML model from disk (only once)."""
    global _trained_model
    if _trained_model is None and os.path.exists(model_path):
        with open(model_path, "rb") as f:
            _trained_model = pickle.load(f)
        print(f"ML Classifier loaded from: {model_path}")
    return _trained_model


def classify_document(text, model_path="app/models/classifier_model.pkl"):
    """
    Main function — call this to classify a document.

    First tries ML model. If not available, uses keyword scoring.

    Returns: "invoice", "receipt", "bank_statement", or "unknown"
    """
    model = _load_model(model_path)

    if model is not None:
        return _classify_with_ml(text, model)
    else:
        print("No ML model found, using keyword matching...")
        return _classify_with_keywords(text)


def _classify_with_ml(text, model):
    """Use the trained sklearn model to classify."""
    try:
        prediction   = model.predict([text])[0]
        confidence   = model.predict_proba([text]).max()

        print(f"ML says: {prediction} (confidence: {confidence:.0%})")

        # If model is not very confident (< 60%), fall back to keywords
        if confidence < 0.60:
            return _classify_with_keywords(text)

        return prediction

    except Exception as e:
        print(f"ML classification error: {e}")
        return _classify_with_keywords(text)


def _classify_with_keywords(text):
    """
    Count how many keywords from each category appear in the text.
    The category with the most keyword matches wins.
    """
    text_lower = text.lower()

    # Count matches for each document type
    scores = {}
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        scores[doc_type] = sum(1 for kw in keywords if kw in text_lower)

    print(f"Keyword scores: {scores}")

    # Find the winner
    best_type  = max(scores, key=scores.get)
    best_score = scores[best_type]

    # If nothing matched, return "unknown"
    return best_type if best_score > 0 else "unknown"


def train_and_save_model(texts, labels, save_path):
    """
    Train the ML classifier and save it to disk.
    Called from train_classifier.py

    Uses TF-IDF + Logistic Regression pipeline:
    - TF-IDF: converts text to numbers (word frequency)
    - Logistic Regression: learns to classify from those numbers
    """
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    # Build the ML pipeline
    pipeline = Pipeline([
        # TF-IDF: "Term Frequency - Inverse Document Frequency"
        # Converts text into a number vector
        ("tfidf", TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),   # use single words AND pairs of words
            sublinear_tf=True     # use log scaling for better results
        )),
        # Logistic Regression classifier
        ("classifier", LogisticRegression(max_iter=1000, C=5.0)),
    ])

    # Cross-validation: tests the model 3 times on different splits
    cv_scores = cross_val_score(pipeline, texts, labels, cv=3, scoring="accuracy")
    print(f"Cross-validation accuracy: {cv_scores.mean():.1%} (±{cv_scores.std():.1%})")

    # Train on all data
    pipeline.fit(texts, labels)

    # Save to disk
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(pipeline, f)

    print(f"Model saved to: {save_path}")
    return pipeline
