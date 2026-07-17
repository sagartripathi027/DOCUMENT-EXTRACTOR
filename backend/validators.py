"""
backend/validators.py

Single source of truth for ALL validation logic.

STRICT RULE: This module contains ONLY:
    - boolean/normalizing validation functions (is_valid_X / normalize_X)
    - each function takes a raw candidate string (already matched by a
      regex in patterns.py) and returns either a cleaned value or None

No regex pattern DEFINITIONS live here (they live in patterns.py).
No extraction/searching logic lives here (that lives in extractor.py).

CHANGELOG (OCR-tolerance refactor):
    - normalize_phone rewritten to actually FORMAT phone numbers
      instead of just passing them through after a length check.
      Behavior:
        * "91-8305671043"      -> "+91 8305671043"
        * "+91 8305671043"     -> "+91 8305671043" (unchanged, just cleaned)
        * "8305671043"         -> "+91 8305671043" (bare 10-digit Indian
                                   mobile, starts with 6-9 -> assume +91)
        * other-length / other-country numbers -> cleaned/collapsed
          but NOT force-relabeled with a guessed country code (avoids
          silently producing a wrong number).
      is_valid_phone's contract (7-15 digits) is preserved so anything
      that already passed as "valid" before still passes now — this
      only changes the OUTPUT FORMAT, not what counts as valid.
"""

import re
from datetime import datetime

from backend.patterns import (
    IGNORE_WORDS,
    EXCLUDE_DOMAINS,
    TECH_TERM_DOMAINS,
    MONTHS,
    PHONE_COUNTRY_CODE_PATTERN,
    PHONE_BARE_INDIAN_10_DIGIT_PATTERN,
)

# =========================================================================
# GENERIC HELPERS
# =========================================================================

def _collapse_spaces(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _digits_only(text):
    return re.sub(r'\D', '', text or '')


# =========================================================================
# NAME VALIDATION
# =========================================================================

def is_valid_name_token(word):
    """A single word is a plausible name token."""
    w = (word or '').strip().upper()
    if not w or w in IGNORE_WORDS:
        return False
    if len(w) < 2:
        return False
    if any(ch.isdigit() for ch in w):
        return False
    return True


def normalize_name(candidate):
    """
    Validate + normalize a name candidate (multi-word string).
    Returns a Title Case name string, or None if invalid.
    """
    if not candidate:
        return None

    words = _collapse_spaces(candidate).split()
    if not words or len(words) > 4:
        return None

    if not all(is_valid_name_token(w) for w in words):
        return None

    if not any(len(w) > 2 for w in words):
        return None

    return " ".join(w.title() for w in words)


# =========================================================================
# EMAIL VALIDATION
# =========================================================================

def is_valid_email(candidate):
    if not candidate:
        return False
    email_re = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_re.match(candidate.strip()))


def normalize_email(candidate):
    if not candidate:
        return None
    cleaned = candidate.strip().lower()
    return cleaned if is_valid_email(cleaned) else None


# =========================================================================
# PHONE VALIDATION
# =========================================================================

def is_valid_phone(candidate):
    digits = _digits_only(candidate)
    return 7 <= len(digits) <= 15


def _format_with_country_code(country_code, subscriber_digits):
    """Build '+<cc> <subscriber>' with no extra internal grouping,
    since source documents use inconsistent grouping and we'd rather
    not invent a grouping that isn't there."""
    return f"+{country_code} {subscriber_digits}"


def normalize_phone(candidate):
    """
    Clean + reformat a phone candidate that already passed pattern
    discovery (PHONE_PATTERN in patterns.py).

    Returns None if the candidate doesn't satisfy is_valid_phone
    (7-15 digits total) — same validity contract as before.

    Otherwise returns a cleaned, human-readable phone string:
      - explicit country code present (with or without '+', with or
        without separators) -> normalized to "+<cc> <rest>"
      - bare 10-digit number starting 6-9 (Indian mobile pattern)
        -> normalized to "+91 <number>"
      - anything else (unrecognized shape/length) -> whitespace-
        collapsed original digits-and-separators, unchanged otherwise,
        to avoid guessing a wrong country code.
    """
    if not candidate:
        return None

    cleaned = _collapse_spaces(candidate)
    if not is_valid_phone(cleaned):
        return None

    digits = _digits_only(cleaned)
    had_plus = cleaned.strip().startswith('+')

    # Case 1: bare 10-digit Indian mobile number, no country code at all
    bare_match = re.match(PHONE_BARE_INDIAN_10_DIGIT_PATTERN, digits)
    if bare_match and not had_plus and len(digits) == 10:
        return _format_with_country_code("91", bare_match.group(1))

    # Case 2: candidate already has (or looks like it has) a country
    # code segment - e.g. "91-8305671043", "+91 8305671043",
    # "0091 8305671043" style inputs land here via the digit count.
    cc_match = re.match(PHONE_COUNTRY_CODE_PATTERN, cleaned.replace(' ', '') if had_plus else cleaned)
    if len(digits) > 10:
        # Try common Indian case explicitly first: leading "91" + 10 digits
        if digits.startswith("91") and len(digits) == 12:
            return _format_with_country_code("91", digits[2:])
        # Generic: assume first 1-3 digits are the country code when
        # total length clearly exceeds a plain national number (>10)
        # and a '+' was present, since that's an explicit signal.
        if had_plus:
            for cc_len in (3, 2, 1):
                if len(digits) - cc_len >= 6:
                    return _format_with_country_code(digits[:cc_len], digits[cc_len:])

    # Case 3: unrecognized shape (e.g. landline w/ STD code, 7-digit
    # extension, unusual length) - return cleaned form as-is rather
    # than guess a country code that might be wrong.
    return cleaned


# =========================================================================
# DATE VALIDATION
# =========================================================================

_MONTH_SET = set(m.lower() for m in MONTHS.split('|'))


def is_plausible_year(year_str):
    try:
        year = int(year_str)
    except (TypeError, ValueError):
        return False
    return 1900 <= year <= 2100


def normalize_date(candidate):
    """
    Light validation for a date candidate. Doesn't force a canonical
    output format (source documents vary too much); just trims noise
    and rejects obvious garbage (e.g. no plausible 4-digit year at all
    for formats that require one).
    """
    if not candidate:
        return None

    cleaned = _collapse_spaces(candidate)

    year_match = re.search(r'\b(\d{4})\b', cleaned)
    if year_match and not is_plausible_year(year_match.group(1)):
        return None

    return cleaned


# =========================================================================
# AMOUNT VALIDATION
# =========================================================================

def normalize_amount(candidate):
    if not candidate:
        return None
    cleaned = _collapse_spaces(candidate)
    if not re.search(r'\d', cleaned):
        return None
    return cleaned


# =========================================================================
# INDIAN GOVERNMENT ID VALIDATION
# =========================================================================

def is_valid_pan(candidate):
    if not candidate:
        return False
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', candidate.strip().upper()))


def normalize_pan(candidate):
    if not candidate:
        return None
    cleaned = candidate.strip().upper()
    return cleaned if is_valid_pan(cleaned) else None


def is_valid_aadhar(candidate):
    if not candidate:
        return False
    digits = _digits_only(candidate)
    return len(digits) == 12 and digits[0] not in ('0', '1')


def normalize_aadhar(candidate):
    if not candidate:
        return None
    digits = _digits_only(candidate)
    if not is_valid_aadhar(digits):
        return None
    return f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"


def is_valid_gstin(candidate):
    if not candidate:
        return False
    return bool(re.match(
        r'^\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]$',
        candidate.strip().upper()
    ))


def normalize_gstin(candidate):
    if not candidate:
        return None
    cleaned = candidate.strip().upper().replace(' ', '')
    return cleaned if is_valid_gstin(cleaned) else None


def is_valid_ifsc(candidate):
    if not candidate:
        return False
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', candidate.strip().upper()))


def normalize_ifsc(candidate):
    if not candidate:
        return None
    cleaned = candidate.strip().upper()
    return cleaned if is_valid_ifsc(cleaned) else None


def normalize_account_number(candidate):
    if not candidate:
        return None
    cleaned = _collapse_spaces(candidate)
    digits = _digits_only(cleaned)
    if len(digits) < 6:
        return None
    return cleaned


# =========================================================================
# URL / SOCIAL VALIDATION
# =========================================================================

def normalize_github(username_or_path):
    if not username_or_path:
        return None
    cleaned = username_or_path.strip().strip('/')
    if not cleaned or '@' in cleaned or cleaned.lower() in ('com', 'in', 'io'):
        return None
    return f"github.com/{cleaned}"


def normalize_linkedin(username):
    if not username:
        return None
    cleaned = username.strip().strip('/')
    if not cleaned or '@' in cleaned or cleaned.lower() in ('com', 'in', 'io'):
        return None
    return f"linkedin.com/in/{cleaned}"


def is_valid_portfolio_url(url, email_domain=None):
    if not url:
        return False

    u_lower = url.lower().rstrip('.,')
    domain = u_lower.split('/')[0]

    if 'github.com' in u_lower or 'linkedin.com' in u_lower:
        return False
    if '@' in url:
        return False
    if domain in EXCLUDE_DOMAINS or domain in TECH_TERM_DOMAINS:
        return False
    if email_domain and domain == email_domain:
        return False
    if not re.search(r'\.(com|in|io|dev|me|org|net|co|app)\b', domain):
        return False

    return True


# =========================================================================
# INVOICE / MISC VALIDATION
# =========================================================================

def normalize_invoice_number(candidate):
    if not candidate:
        return None
    cleaned = candidate.strip().strip('-/')
    return cleaned if cleaned else None


def normalize_pincode(candidate):
    digits = _digits_only(candidate)
    return digits if len(digits) == 6 else None


def normalize_generic_text(candidate, min_len=2, max_len=150):
    """Fallback normalizer for generic/custom fields with no dedicated rule."""
    if not candidate:
        return None
    cleaned = _collapse_spaces(candidate)
    if not (min_len <= len(cleaned) <= max_len):
        return None
    return cleaned