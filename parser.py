"""
parser.py

Coordinates extraction. Contains NO regex of its own — all patterns
live in backend/patterns.py, all validation in backend/validators.py,
all per-field logic in backend/extractor.py, and all name/alias
resolution in backend/field_mapper.py.

This module exposes TWO entry points:

    1. parse_structured_data(text)
       -> Preserved for backward compatibility. Returns the exact
          same dict shape the original parser.py produced, so any
          existing caller (or the current app.py route) keeps working
          unmodified.

    2. parse_requested_fields(text, requested_fields)
       -> New universal entry point. Given raw OCR text and a list of
          user-requested field names (any casing/aliases), returns a
          dict containing ONLY those fields, using field_mapper.py to
          resolve names to extractors and extractor.py to run them.

Nothing here is document-type-specific (no "resume" or "invoice"
branching) — the SAME extractors serve every document type. What
changes per document is only which fields the caller requests.
"""

from backend import extractor as ext
from backend import field_mapper as fm


# =========================================================================
# BACKWARD-COMPATIBLE ENTRY POINT
# =========================================================================

def parse_structured_data(text):
    """
    PRESERVED for backward compatibility with the existing API
    response shape (used by the current /extract route as-is).

    Returns the same dict keys the original parser.py returned:
        dates, amounts, email, phones, github, linkedin, portfolio,
        names, raw_text
    """
    email = ext.extract_email(text)
    email_domain = email.split('@')[1].lower() if email else None

    data = {
        "dates": ext.extract_dates(text),
        "amounts": ext.extract_amounts(text),
        "email": email,
        "phones": ext.extract_phones(text),
        "github": ext.extract_github(text),
        "linkedin": ext.extract_linkedin(text),
        "portfolio": ext.extract_portfolio(text, email_domain=email_domain),
        "names": ext.extract_names(text),
        "raw_text": text,
    }

    return data


# =========================================================================
# UNIVERSAL / NEW ENTRY POINT
# =========================================================================

def parse_requested_fields(text, requested_fields):
    """
    Extract ONLY the fields the caller asked for.

    Args:
        text: raw OCR text (already produced by processor.py — parser
              never touches OCR/image logic).
        requested_fields: iterable of user-supplied field name strings,
              e.g. ["Name", "Email", "GST", "Father's Name"].
              Case-insensitive; aliases are resolved via field_mapper.

    Returns:
        dict mapping canonical field key -> extracted value
        (str | list | None), containing exactly one entry per
        requested field (deduplicated, order-preserving).

    Unknown fields (no dedicated extractor/alias registered) are
    handled generically: the raw user-supplied name itself becomes
    the label alias searched for in the text via
    extractor.extract_custom_field.
    """
    if not requested_fields:
        return {}

    # Email is needed as context for portfolio-domain exclusion; only
    # compute it if actually relevant, but cheaply cache if requested.
    email_cache = {"computed": False, "value": None}

    def _get_email_domain():
        if not email_cache["computed"]:
            email_val = ext.extract_email(text)
            email_cache["value"] = email_val.split('@')[1].lower() if email_val else None
            email_cache["computed"] = True
        return email_cache["value"]

    results = {}
    seen_keys = set()

    for raw_field_name in requested_fields:
        if not raw_field_name or not raw_field_name.strip():
            continue

        field_def = fm.resolve_field(raw_field_name)
        canonical_key = fm.normalize_field_key(raw_field_name)

        if canonical_key in seen_keys:
            continue
        seen_keys.add(canonical_key)

        if field_def is not None:
            # Special-case the one extractor that needs extra context
            # (portfolio needs email domain to avoid false positives).
            if field_def.extractor is ext.extract_portfolio:
                value = ext.extract_portfolio(text, email_domain=_get_email_domain())
            else:
                value = field_def.extractor(text)
        else:
            # Unknown/custom field -> generic labeled-value fallback,
            # using the user's own wording as the alias to search for.
            value = ext.extract_custom_field(text, aliases=[raw_field_name.strip()])

        results[canonical_key] = value

    return results


# =========================================================================
# INTROSPECTION HELPER (useful for a future "list supported fields"
# endpoint, without app.py needing to know about field_mapper directly)
# =========================================================================

def get_supported_fields():
    return fm.list_supported_fields()