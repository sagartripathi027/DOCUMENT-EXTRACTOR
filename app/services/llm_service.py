# ============================================================
#  llm_service.py — Use GPT to Fix and Improve Extracted Data
#
#  LLM = Large Language Model (GPT-4o-mini here)
#  RAG = Retrieval Augmented Generation
#
#  What this module does:
#    1. Takes raw OCR text + fields extracted by NER
#    2. Sends them to GPT with a smart prompt
#    3. GPT fixes errors, fills missing fields, normalizes formats
#    4. Also uses RAG: looks up similar past documents to help GPT
#
#  RAG Vector Store:
#    - We store past processed documents as "embeddings" (number vectors)
#    - When a new document comes in, we find the most similar past docs
#    - We give those to GPT as examples → better accuracy
# ============================================================

import os
import json

# Global variables (cached so we don't reload every request)
_openai_client   = None
_vector_store    = None


# ── OPENAI CLIENT ─────────────────────────────────────────────────────────────

def _get_openai():
    """Get OpenAI client (created once and reused)."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or "your-" in key:
            raise ValueError("Please set your OPENAI_API_KEY in the .env file!")
        _openai_client = OpenAI(api_key=key)
    return _openai_client


# ── RAG VECTOR STORE ──────────────────────────────────────────────────────────

def _get_vector_store(store_path):
    """Load FAISS vector store from disk (if it exists)."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    try:
        import faiss
        from sentence_transformers import SentenceTransformer

        index_file = os.path.join(store_path, "index.faiss")
        meta_file  = os.path.join(store_path, "metadata.json")

        if os.path.exists(index_file) and os.path.exists(meta_file):
            # Load FAISS index (stores document vectors)
            index = faiss.read_index(index_file)

            # Load metadata (stores the actual field data)
            with open(meta_file) as f:
                metadata = json.load(f)

            # Load the sentence transformer (converts text → vectors)
            embedder = SentenceTransformer("all-MiniLM-L6-v2")

            _vector_store = {
                "index":    index,
                "metadata": metadata,
                "embedder": embedder
            }
            print(f"RAG vector store loaded: {index.ntotal} past documents")

    except Exception as e:
        print(f"Could not load vector store: {e}")

    return _vector_store


def _find_similar_documents(text, store_path, top_k=2):
    """
    Find the most similar past documents using vector search.

    How it works:
    1. Convert our text to a vector (list of numbers)
    2. Search FAISS for the closest vectors
    3. Return the metadata (fields) of those documents
    """
    store = _get_vector_store(store_path)
    if store is None:
        return ""  # No vector store yet

    try:
        # Convert text to vector
        vector = store["embedder"].encode([text], convert_to_numpy=True)

        # Search for top-k nearest neighbors
        _, indices = store["index"].search(vector.astype("float32"), top_k)

        # Collect matching documents
        examples = []
        for idx in indices[0]:
            if 0 <= idx < len(store["metadata"]):
                examples.append(json.dumps(store["metadata"][idx], indent=2))

        return "\n---\n".join(examples)

    except Exception as e:
        print(f"RAG search failed: {e}")
        return ""


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def correct_and_normalize(raw_text, doc_type, extracted_fields, store_path="data/vector_store"):
    """
    Send extracted fields to GPT for correction and normalization.

    GPT will:
    - Fix wrong field values
    - Fill in missing fields it can find in the text
    - Convert all dates to YYYY-MM-DD format
    - Convert all amounts to plain numbers (remove ₹ $ symbols)

    Returns the corrected fields as a dictionary.
    """

    # Get similar past documents for RAG context
    similar_docs = _find_similar_documents(raw_text, store_path)
    rag_section  = f"\nExamples from similar past documents:\n{similar_docs}" if similar_docs else ""

    # Build the prompt for GPT
    prompt = f"""You are a document data extraction assistant for a college project.

Document Type: {doc_type}

Raw OCR Text (the actual document content):
\"\"\"
{raw_text[:2000]}
\"\"\"

Fields already extracted by our NER model (may have errors):
{json.dumps(extracted_fields, indent=2, default=str)}
{rag_section}

Your job:
1. Look at the raw OCR text carefully
2. Fix any wrong field values
3. Fill in missing fields if the info is clearly in the text
4. Convert ALL dates to format: YYYY-MM-DD
5. Convert ALL amounts to plain float numbers (no ₹ $ symbols or commas)
6. If a field is not found, set it to null
7. Do NOT make up information that is not in the text

IMPORTANT: Reply with ONLY a valid JSON object. No explanation text. No markdown.

JSON:"""

    try:
        client   = _get_openai()
        response = client.chat.completions.create(
            model="gpt-4o-mini",       # Cheapest GPT model, still very good
            messages=[{"role": "user", "content": prompt}],
            temperature=0,             # 0 = deterministic, no hallucinations
            max_tokens=600,
            timeout=30,
        )

        # Get the response text
        answer = response.choices[0].message.content.strip()

        # Remove markdown code fences if GPT added them
        answer = answer.replace("```json", "").replace("```", "").strip()

        # Parse as JSON
        corrected_fields = json.loads(answer)
        print("GPT correction successful!")
        return corrected_fields

    except json.JSONDecodeError:
        print("GPT returned invalid JSON, using original fields")
        return extracted_fields

    except Exception as e:
        print(f"GPT correction failed: {e}")
        # If GPT fails, just return what NER extracted
        extracted_fields["_note"] = f"GPT unavailable: {str(e)[:60]}"
        return extracted_fields


def save_to_vector_store(doc_text, fields, store_path):
    """
    Save this processed document to the RAG vector store.
    Next time a similar document is processed, GPT will use this as an example.

    How it works:
    1. Convert document text → vector (embedding)
    2. Add vector to FAISS index
    3. Save fields to metadata file
    """
    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer

        os.makedirs(store_path, exist_ok=True)
        index_file = os.path.join(store_path, "index.faiss")
        meta_file  = os.path.join(store_path, "metadata.json")

        # Create embedding
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        vector   = embedder.encode([doc_text], convert_to_numpy=True).astype("float32")

        # Load existing store or create new one
        if os.path.exists(index_file) and os.path.exists(meta_file):
            index    = faiss.read_index(index_file)
            with open(meta_file) as f:
                metadata = json.load(f)
        else:
            # First time: create a new FAISS index
            # 384 = dimension of all-MiniLM-L6-v2 embeddings
            index    = faiss.IndexFlatL2(vector.shape[1])
            metadata = []

        # Add new document
        index.add(vector)
        clean_fields = {k: v for k, v in fields.items() if not k.startswith("_")}
        metadata.append(clean_fields)

        # Save to disk
        faiss.write_index(index, index_file)
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Reset cache so next request loads fresh data
        global _vector_store
        _vector_store = None

        print(f"Saved to vector store. Total docs: {index.ntotal}")

    except Exception as e:
        print(f"Could not save to vector store: {e}")
