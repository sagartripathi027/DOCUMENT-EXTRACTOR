"""
backend/extractor.py

One function per extractable field. Each function is:
    - independent  (no function calls another field's extractor)
    - reusable     (pure function: text in -> value out)
    - side-effect free

Functions consume patterns from patterns.py and validate/normalize
results using validators.py. They never define regex inline for
anything that belongs in patterns.py.

Return contract:
    - "single value" fields (name, email, company, invoice_number, ...)
        -> str | None
    - "multi value" fields (dates, amounts, skills, phones, ...)
        -> list[str]  (possibly empty)

parser.py orchestrates which of these get called based on the
user's requested fields (via field_mapper.py). app.py never touches
this module directly.
"""

import re

from backend import patterns as pat
from backend import validators as val


# =========================================================================
# INTERNAL HELPERS (not extractors themselves — used by several of them)
# =========================================================================

def _normalize_text(text):
    """Collapse whitespace/newlines the way all extractors expect."""
    norm = re.sub(r'[ \t]+', ' ', text or '')
    norm = re.sub(r'\s*\n\s*', ' ', norm)
    norm = re.sub(r'\s+', ' ', norm).strip()
    return norm


def _apply_email_ocr_fixes(text):
    fixed = text
    for search, replace in pat.EMAIL_OCR_FIX_PATTERNS:
        fixed = re.sub(search, replace, fixed, flags=re.IGNORECASE)
    return fixed


def _find_labeled_value(text, label_pattern):
    """Run a `label: value` style pattern and return the first capture, or None."""
    match = re.search(label_pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _find_all(pattern, text, flags=re.IGNORECASE):
    return re.findall(pattern, text, flags)


def _dedupe_preserve_order(items):
    return list(dict.fromkeys(i for i in items if i))


def _section_block(text, section_key):
    """
    Extract the free-text block following a known section header
    (e.g. "Education") up until the next known section header begins.
    Returns raw block string or None.
    """
    headers = pat.SECTION_HEADERS.get(section_key)
    if not headers:
        return None

    other_headers = []
    for key, labels in pat.SECTION_HEADERS.items():
        if key != section_key:
            other_headers.extend(labels)

    section_alt = "|".join(re.escape(h) for h in headers)
    next_alt = "|".join(re.escape(h) for h in other_headers) or r'(?!x)x'  # never matches if empty

    pattern = pat.SECTION_BLOCK_PATTERN_TEMPLATE.format(
        section=section_alt, next_sections=next_alt
    )
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    block = match.group(1).strip(" :-\t\n")
    return block if block else None


# =========================================================================
# NAME
# =========================================================================

def extract_names(raw_text):
    """Returns list[str] of plausible full names found in the document."""
    text = _normalize_text(raw_text)
    candidates = []

    # Explicit "Name: ..." label takes priority
    labeled = _find_labeled_value(text, pat.NAME_LABEL_PATTERN)
    if labeled:
        normalized = val.normalize_name(labeled)
        if normalized:
            candidates.append((0, normalized))

    for m in re.finditer(pat.NAME_CAPS_PATTERN, text):
        normalized = val.normalize_name(m.group())
        if normalized:
            candidates.append((m.start(), normalized))

    for m in re.finditer(pat.NAME_TITLE_PATTERN, text):
        normalized = val.normalize_name(re.sub(r'^Name[:\-]\s*', '', m.group()))
        if normalized:
            candidates.append((m.start(), normalized))

    candidates.sort(key=lambda x: x[0])

    seen = set()
    result = []
    for _, c in candidates:
        key = c.upper()
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def extract_name(raw_text):
    """Single best-guess name (first valid candidate), for callers that want str | None."""
    names = extract_names(raw_text)
    return names[0] if names else None


# =========================================================================
# CONTACT
# =========================================================================

def extract_email(raw_text):
    text = _normalize_text(raw_text)
    fixed = _apply_email_ocr_fixes(text)

    match = re.search(pat.EMAIL_PATTERN, fixed)
    if match:
        normalized = val.normalize_email(match.group())
        if normalized:
            return normalized

    fallback = re.search(pat.EMAIL_PATTERN, text)
    if fallback:
        return val.normalize_email(fallback.group())

    return None


def extract_phones(raw_text):
    text = _normalize_text(raw_text)
    candidates = []

    labeled = _find_labeled_value(text, pat.LABELED_PHONE_PATTERN)
    if labeled:
        candidates.append(labeled)

    candidates.extend(_find_all(pat.PHONE_PATTERN, text))

    normalized = [val.normalize_phone(c) for c in candidates]
    return _dedupe_preserve_order([n for n in normalized if n])


def extract_address(raw_text):
    text = _normalize_text(raw_text)

    labeled = _find_labeled_value(text, pat.ADDRESS_LABEL_PATTERN)
    if labeled:
        return val.normalize_generic_text(labeled, min_len=5, max_len=200)

    block = _section_block(text, "address")
    if block:
        return val.normalize_generic_text(block, min_len=5, max_len=200)

    return None


# =========================================================================
# SOCIAL / URLS
# =========================================================================

def extract_github(raw_text):
    text = _normalize_text(raw_text)
    results = []

    for m in re.finditer(pat.GITHUB_URL_PATTERN, text, re.IGNORECASE):
        normalized = val.normalize_github(m.group(1))
        if normalized:
            results.append(normalized)

    for m in re.finditer(pat.GITHUB_LABEL_PATTERN, text, re.IGNORECASE):
        normalized = val.normalize_github(m.group(1))
        if normalized:
            results.append(normalized)

    return _dedupe_preserve_order(results)


def extract_linkedin(raw_text):
    text = _normalize_text(raw_text)
    results = []

    for m in re.finditer(pat.LINKEDIN_URL_PATTERN, text, re.IGNORECASE):
        normalized = val.normalize_linkedin(m.group(1))
        if normalized:
            results.append(normalized)

    for m in re.finditer(pat.LINKEDIN_LABEL_PATTERN, text, re.IGNORECASE):
        normalized = val.normalize_linkedin(m.group(1))
        if normalized:
            results.append(normalized)

    return _dedupe_preserve_order(results)


def extract_portfolio(raw_text, email_domain=None):
    text = _normalize_text(raw_text)
    all_urls = _find_all(pat.GENERIC_URL_PATTERN, text)

    results = [
        u for u in all_urls
        if val.is_valid_portfolio_url(u, email_domain=email_domain)
    ]
    return _dedupe_preserve_order(results)


# =========================================================================
# DATES / AMOUNTS
# =========================================================================

def extract_dates(raw_text):
    text = _normalize_text(raw_text)
    matches = []

    for pattern in pat.DATE_PATTERNS:
        matches.extend(_find_all(pattern, text))

    normalized = [val.normalize_date(m) for m in matches]
    return _dedupe_preserve_order([n for n in normalized if n])


def extract_amounts(raw_text):
    text = _normalize_text(raw_text)
    matches = _find_all(pat.AMOUNT_PATTERN, text)
    matches.extend(_find_all(pat.OLD_AMOUNT_PATTERN, text))

    normalized = [val.normalize_amount(m) for m in matches]
    return _dedupe_preserve_order([n for n in normalized if n])


def extract_total_amount(raw_text):
    """Best-guess single 'grand total / amount due' style value."""
    text = _normalize_text(raw_text)
    labeled = _find_labeled_value(text, pat.TOTAL_AMOUNT_LABEL_PATTERN)
    return val.normalize_amount(labeled) if labeled else None


# =========================================================================
# INDIAN GOVERNMENT IDS
# =========================================================================

def extract_pan(raw_text):
    text = _normalize_text(raw_text)

    labeled = _find_labeled_value(text, pat.PAN_LABEL_PATTERN)
    normalized = val.normalize_pan(labeled) if labeled else None
    if normalized:
        return normalized

    match = re.search(pat.PAN_PATTERN, text)
    return val.normalize_pan(match.group()) if match else None


def extract_aadhar(raw_text):
    text = _normalize_text(raw_text)

    labeled = _find_labeled_value(text, pat.AADHAR_LABEL_PATTERN)
    normalized = val.normalize_aadhar(labeled) if labeled else None
    if normalized:
        return normalized

    match = re.search(pat.AADHAR_PATTERN, text)
    return val.normalize_aadhar(match.group()) if match else None


def extract_gst(raw_text):
    text = _normalize_text(raw_text)

    labeled = _find_labeled_value(text, pat.GSTIN_LABEL_PATTERN)
    normalized = val.normalize_gstin(labeled) if labeled else None
    if normalized:
        return normalized

    match = re.search(pat.GSTIN_PATTERN, text)
    return val.normalize_gstin(match.group()) if match else None


def extract_ifsc(raw_text):
    text = _normalize_text(raw_text)
    match = re.search(pat.IFSC_PATTERN, text)
    return val.normalize_ifsc(match.group()) if match else None


def extract_account_number(raw_text):
    text = _normalize_text(raw_text)
    labeled = _find_labeled_value(text, pat.ACCOUNT_NUMBER_LABEL_PATTERN)
    return val.normalize_account_number(labeled) if labeled else None


# =========================================================================
# INVOICE / BILLING
# =========================================================================

def extract_invoice_number(raw_text):
    text = _normalize_text(raw_text)
    labeled = _find_labeled_value(text, pat.INVOICE_NUMBER_LABEL_PATTERN)
    return val.normalize_invoice_number(labeled) if labeled else None


def extract_pincode(raw_text):
    text = _normalize_text(raw_text)
    match = re.search(pat.PINCODE_PATTERN, text)
    return val.normalize_pincode(match.group()) if match else None


# =========================================================================
# RESUME-STYLE SECTIONS (generic — not resume-specific logic, just
# reusable "section block" extraction applied to common section names)
# =========================================================================

def extract_company(raw_text):
    text = _normalize_text(raw_text)

    labeled = _find_labeled_value(text, pat.COMPANY_LABEL_PATTERN)
    if labeled:
        return val.normalize_generic_text(labeled, min_len=2, max_len=100)

    return None


def extract_skills(raw_text):
    text = _normalize_text(raw_text)
    block = _section_block(text, "skills")

    if block:
        parts = re.split(r'[,;|/•]+', block)
        skills = [val.normalize_generic_text(p, min_len=2, max_len=40) for p in parts]
        return _dedupe_preserve_order([s for s in skills if s])

    # Fallback: scan for known skill keywords anywhere in the document
    lowered = text.lower()
    found = [kw for kw in pat.SKILL_KEYWORDS if kw in lowered]
    return _dedupe_preserve_order(found)


def extract_education(raw_text):
    text = _normalize_text(raw_text)
    block = _section_block(text, "education")
    return val.normalize_generic_text(block, min_len=3, max_len=500) if block else None


def extract_experience(raw_text):
    text = _normalize_text(raw_text)
    block = _section_block(text, "experience")
    return val.normalize_generic_text(block, min_len=3, max_len=500) if block else None


def extract_projects(raw_text):
    text = _normalize_text(raw_text)
    block = _section_block(text, "projects")
    return val.normalize_generic_text(block, min_len=3, max_len=500) if block else None


# =========================================================================
# GENERIC / CUSTOM FIELD FALLBACK
# =========================================================================

def extract_custom_field(raw_text, aliases):
    """
    Generic extractor used for any user-supplied field that has no
    dedicated extractor function above. `aliases` is a list of label
    strings (e.g. ["father name", "father's name"]) supplied by
    field_mapper.py.
    """
    text = _normalize_text(raw_text)
    pattern = pat.generic_field_pattern(aliases)
    labeled = _find_labeled_value(text, pattern)
    return val.normalize_generic_text(labeled) if labeled else None