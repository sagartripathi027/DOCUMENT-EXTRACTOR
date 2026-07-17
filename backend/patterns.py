"""
backend/patterns.py

Single source of truth for ALL regular expressions and static
pattern-support data used across the extraction engine.

STRICT RULE: This module contains ONLY:
    - regex pattern strings / compiled patterns
    - static lookup data that regexes depend on (word lists, domain lists)
    - tiny, side-effect-free helpers that BUILD regex patterns
      (no validation, no extraction, no business logic)

extractor.py consumes these patterns. validators.py validates the
matches these patterns produce. Nothing in this file should know
about "documents", "fields", or user input.

CHANGELOG (OCR-tolerance refactor):
    - GITHUB_LABEL_PATTERN / LINKEDIN_LABEL_PATTERN widened to accept
      common OCR splits/variants ("Git Hub", "Git-Hub", "Linked In",
      "Linked-in", etc.) without touching the URL-based patterns.
    - Added PHONE_COUNTRY_CODE_PATTERN: a structured capture (country
      code + subscriber number) used by validators.normalize_phone to
      reformat "91-8305671043" -> "+91 8305671043". PHONE_PATTERN
      itself (used for raw candidate discovery) is unchanged so
      existing match behavior/order is preserved.
"""

import re

# =========================================================================
# GENERIC HELPERS (pattern builders only — no extraction logic)
# =========================================================================

def build_label_pattern(labels, value_pattern=r'[^\n,;|]{2,80}', flags_str=True):
    """
    Build a regex pattern (string) that matches: <label> [:/-]? <value>

    labels: iterable of label alternatives, e.g. ["invoice no", "inv no"]
    value_pattern: regex fragment for the value portion.

    Returns a raw pattern STRING (not compiled), so callers can compose
    or compile with whatever flags they need.
    """
    label_alt = "|".join(re.escape(l) for l in labels) if not flags_str else "|".join(labels)
    return rf'(?:{label_alt})\s*[:\-]?\s*({value_pattern})'


def compile_all(pattern_list, flags=re.IGNORECASE):
    """Compile a list of raw pattern strings, skipping ones already compiled."""
    compiled = []
    for p in pattern_list:
        if isinstance(p, re.Pattern):
            compiled.append(p)
        else:
            compiled.append(re.compile(p, flags))
    return compiled


# =========================================================================
# SHARED STATIC DATA
# =========================================================================

MONTHS = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)

IGNORE_WORDS = {
    "AWS", "TCS", "CERTIFICATE", "COMPLETION", "ARCHITECTURE", "SOLUTIONS",
    "SIMULATION", "JOB", "RESUME", "CURRICULUM", "VITAE", "PROFILE",
    "OBJECTIVE", "SUMMARY", "EDUCATION", "EXPERIENCE", "SKILLS", "PROJECTS",
    "CONTACT", "ADDRESS", "PHONE", "EMAIL", "LINKEDIN", "GITHUB", "PORTFOLIO",
    "DECLARATION", "REFERENCES", "ACHIEVEMENTS", "CERTIFICATIONS", "TRAINING",
    "INTERNSHIP", "COURSE", "PROGRAM", "SIMULATED", "PRACTICAL", "TASKS",
    "MODULE", "COMPANY", "TEAM", "DEPARTMENT", "UNIVERSITY", "COLLEGE",
    "INSTITUTE", "SCHOOL", "BOARD", "INDIA", "LTD", "PVT", "INC", "LLC",
    "GOOGLE", "MICROSOFT", "AMAZON", "IBM", "ACCENTURE", "INFOSYS", "WIPRO",
    "COGNIZANT", "CAPGEMINI", "DELOITTE", "COURSERA", "UDEMY", "FORAGE",
    "AI", "ML", "BI", "MS", "IT", "OS", "UI", "UX", "QA", "HR", "PR",
    "CEO", "CTO", "CFO", "SQL", "API", "REST", "JSON", "XML", "HTML", "CSS",
    "PDF", "OCR", "NLP", "EDA", "GPA", "CGPA", "USA", "UK", "RGPV", "MP",
    "TECHNICAL", "LANGUAGES", "FRAMEWORKS", "DATABASES", "TOOLS", "ANALYTICS",
    "CLEANING", "STATISTICAL", "ANALYSIS", "VISUALIZATION", "EXCEL",
    "PYTHON", "JAVASCRIPT", "FLASK", "FASTAPI", "APIS", "PANDAS", "NUMPY",
    "TESSERACT", "MYSQL", "POSTGRESQL", "MONGODB", "GIT", "DOCKER",
    "KUBERNETES", "POSTMAN", "MACHINE", "LEARNING", "REGRESSION",
    "CLASSIFICATION", "SCIENCE", "ENGINEERING", "BACKEND", "DATA",
    "UNDERGRADUATE", "COMPUTER", "CBSE", "JBP", "LMS", "CGF", "CLASS",
    "INVOICE", "BILL", "RECEIPT", "STATEMENT", "BANK", "ACCOUNT", "BRANCH",
    "IFSC", "GSTIN", "PAN", "AADHAR", "AADHAAR", "CARD", "GOVERNMENT",
    "DISTRICT", "STATE", "PINCODE", "PIN", "TOTAL", "SUBTOTAL", "TAX",
    "GST", "CGST", "SGST", "IGST", "AMOUNT", "DATE", "DUE", "PAID",
}

EXCLUDE_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com",
    "icloud.com", "live.com", "protonmail.com", "yahoo.co.in", "aol.com",
}

TECH_TERM_DOMAINS = {
    "socket.io", "node.js", "vue.js", "react.js", "d3.js", "express.js",
    "next.js", "nuxt.js", "three.js", "chart.js", "ember.js", "backbone.js",
    "angular.js", "jquery.js", "webpack.js",
}

# Common skill keywords used to recover a "Skills" block even when the
# section header itself is OCR-mangled. Purely data — no logic.
SKILL_KEYWORDS = {
    "python", "java", "c++", "c#", "javascript", "typescript", "html",
    "css", "sql", "nosql", "react", "angular", "vue", "node", "django",
    "flask", "fastapi", "spring", "pandas", "numpy", "tensorflow",
    "pytorch", "keras", "scikit-learn", "excel", "power bi", "tableau",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "github",
    "linux", "mongodb", "mysql", "postgresql", "rest api", "graphql",
    "machine learning", "deep learning", "nlp", "data analysis",
    "communication", "leadership", "teamwork", "problem solving",
}

SECTION_HEADERS = {
    "education": ["education", "academic background", "qualification", "qualifications"],
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "projects": ["projects", "academic projects", "personal projects"],
    "skills": ["skills", "technical skills", "key skills", "core competencies"],
    "address": ["address", "residential address", "permanent address", "current address"],
    "company": ["company", "organization", "organisation", "employer"],
}


# =========================================================================
# DATE PATTERNS
# =========================================================================

DATE_PATTERNS = [
    r'\d{4}[-/]\d{2}[-/]\d{2}',
    r'\d{2}[-/]\d{2}[-/]\d{4}',
    r'\b\d{8}\b',
    rf'\b(?:{MONTHS})[a-zA-Z]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b',
    rf'\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})[a-zA-Z]*\.?,?\s+\d{{4}}\b',
    rf'\b(?:{MONTHS})[a-zA-Z]*\.?\s+\d{{4}}\b',
    r'\b\d{4}\s*-\s*\d{4}\b',
]

DATE_PATTERNS_CLEAN_ONLY = [
    r'\d{4}[-/]\d{2}[-/]\d{2}',
    r'\d{2}[-/]\d{2}[-/]\d{4}',
    r'\b\d{8}\b',
]

# Due date / issue date / valid-till style labeled dates (invoices, IDs, certs)
LABELED_DATE_PATTERN = build_label_pattern(
    labels=[
        "date of issue", "issue date", "issued on", "date of birth", "dob",
        "valid till", "valid until", "expiry date", "expiration date",
        "due date", "invoice date", "bill date", "date",
    ],
    value_pattern=r'[0-9A-Za-z,./\- ]{6,20}',
)


# =========================================================================
# AMOUNT / CURRENCY PATTERNS
# =========================================================================

AMOUNT_PATTERN = r'(?:₹|Rs\.?\s?|INR\s?|\$|€)\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?'
OLD_AMOUNT_PATTERN = r'\d{3,}(?:[.,]\d{2})'

TOTAL_AMOUNT_LABEL_PATTERN = build_label_pattern(
    labels=[
        "grand total", "total amount", "amount due", "balance due",
        "net payable", "total payable", "total",
    ],
    value_pattern=r'(?:₹|Rs\.?\s?|INR\s?|\$|€)?\s?\d[\d,]*(?:\.\d{1,2})?',
)


# =========================================================================
# EMAIL PATTERNS (+ OCR error fixers)
# =========================================================================

EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

EMAIL_OCR_FIX_PATTERNS = [
    (r'\s*@\s*', '@'),
    (r'\s*\.\s*(com|in|org|net|co|edu|io)\b', r'.\1'),
    (
        r'@\s*(gmail|yahoo|outlook|hotmail|rediffmail|icloud)\s*(?:\.|,)?\s*(com|in|co\.in|net)\b',
        r'@\1.\2',
    ),
    (
        r'([a-zA-Z0-9._%+-]+)\s*\(?\bat\b\)?\s*(gmail|yahoo|outlook|hotmail|rediffmail|icloud)\s*\(?\bdot\b\)?\s*(com|in|co\.in|net)',
        r'\1@\2.\3',
    ),
    (
        r'([a-zA-Z0-9._%+-]+)@(gmail|yahoo|outlook|hotmail|rediffmail|icloud)(com|in|net)\b',
        r'\1@\2.\3',
    ),
]


# =========================================================================
# PHONE PATTERNS
# =========================================================================

# Raw candidate discovery pattern — UNCHANGED from the original, so
# existing match order/positions in extractor.extract_phones are
# preserved exactly. Formatting/normalization is handled separately.
PHONE_PATTERN = (
    r'(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{2,5}\)[-.\s]?)?'
    r'\d{3,5}[-.\s]?\d{3,4}(?:[-.\s]?\d{2,4})?'
)

LABELED_PHONE_PATTERN = build_label_pattern(
    labels=["phone", "mobile", "contact no", "contact number", "tel", "telephone", "cell"],
    value_pattern=r'[\d+()\-.\s]{7,17}',
)

# NEW: structured capture used only by validators.normalize_phone to
# reformat a candidate that already passed PHONE_PATTERN discovery.
# Group 1 = optional country code digits (1-3), Group 2 = the rest of
# the digits. This does NOT replace PHONE_PATTERN for discovery.
PHONE_COUNTRY_CODE_PATTERN = r'^\+?(\d{1,3})[-.\s]?(\d{6,12})$'

# Bare 10-digit Indian mobile number (no country code present at all).
# Indian mobile numbers start with 6-9.
PHONE_BARE_INDIAN_10_DIGIT_PATTERN = r'^([6-9]\d{9})$'


# =========================================================================
# SOCIAL / URL PATTERNS
# =========================================================================

GITHUB_URL_PATTERN = r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)?)'

# OCR-tolerant label pattern: accepts "github", "git hub", "git-hub",
# "git_hub" (any spacing/hyphen/underscore between the two syllables),
# case-insensitively, optionally followed by "profile"/"id"/"link"/"url".
# URL-based extraction (GITHUB_URL_PATTERN above) is untouched.
GITHUB_LABEL_PATTERN = (
    r'\bgit[\s\-_]?hub\b(?:\s*(?:profile|id|username|link|url))?'
    r'\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9_-]{1,38})'
)

LINKEDIN_URL_PATTERN = r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/([A-Za-z0-9_-]+)/?'

# OCR-tolerant label pattern: accepts "linkedin", "linked in",
# "linked-in", "linked_in", case-insensitively, optionally followed by
# "profile"/"id"/"link"/"url". URL-based extraction untouched.
LINKEDIN_LABEL_PATTERN = (
    r'\blinked[\s\-_]?in\b(?:\s*(?:profile|id|username|link|url))?'
    r'\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9_-]{1,38})'
)

GENERIC_URL_PATTERN = r'(?:https?://)?(?:www\.)?[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?'
PORTFOLIO_DOMAIN_SUFFIX_PATTERN = r'\.(com|in|io|dev|me|org|net|co|app)\b'


# =========================================================================
# NAME PATTERNS
# =========================================================================

NAME_CAPS_PATTERN = r'\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,3}\b'
NAME_TITLE_PATTERN = r'(?:Name[:\-]\s*)?\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
NAME_LABEL_PATTERN = build_label_pattern(
    labels=["name", "full name", "candidate name", "applicant name"],
    value_pattern=r"[A-Za-z][A-Za-z .'\-]{2,60}",
)


# =========================================================================
# INDIAN GOVERNMENT ID PATTERNS
# =========================================================================

PAN_PATTERN = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
PAN_LABEL_PATTERN = build_label_pattern(
    labels=["pan", "pan no", "pan number", "permanent account number"],
    value_pattern=r'[A-Z]{5}[0-9]{4}[A-Z]',
)

# 12 digits, optionally grouped as 4-4-4 with space/hyphen
AADHAR_PATTERN = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
AADHAR_LABEL_PATTERN = build_label_pattern(
    labels=["aadhar", "aadhaar", "aadhar no", "aadhaar number", "uid"],
    value_pattern=r'\d[\d\s-]{10,17}\d',
)

# 15-char GSTIN: 2 digits state code + 10 char PAN + 1 entity + 1 'Z' + 1 checksum
GSTIN_PATTERN = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b'
GSTIN_LABEL_PATTERN = build_label_pattern(
    labels=["gstin", "gst no", "gst number", "gst"],
    value_pattern=r'[0-9A-Z]{15}',
)

IFSC_PATTERN = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
ACCOUNT_NUMBER_LABEL_PATTERN = build_label_pattern(
    labels=["account no", "account number", "a/c no", "a/c number"],
    value_pattern=r'[\dXx\-\s]{6,20}',
)


# =========================================================================
# INVOICE / BILLING PATTERNS
# =========================================================================

INVOICE_NUMBER_LABEL_PATTERN = build_label_pattern(
    labels=[
        "invoice no", "invoice number", "invoice #", "inv no", "inv#",
        "bill no", "bill number", "receipt no", "receipt number",
    ],
    value_pattern=r'[A-Za-z0-9/\-]{2,30}',
)


# =========================================================================
# ADDRESS / COMPANY / SECTION PATTERNS
# =========================================================================

ADDRESS_LABEL_PATTERN = build_label_pattern(
    labels=SECTION_HEADERS["address"],
    value_pattern=r'[^\n]{5,150}',
)

PINCODE_PATTERN = r'\b\d{6}\b'

COMPANY_LABEL_PATTERN = build_label_pattern(
    labels=SECTION_HEADERS["company"] + ["employer name"],
    value_pattern=r'[A-Za-z0-9&.,\- ]{2,80}',
)

# Generic "section until next known section header" style pattern.
# {section} is filled dynamically by extractor.py with an alternation
# of that section's header labels; {next_sections} similarly.
SECTION_BLOCK_PATTERN_TEMPLATE = (
    r'(?:{section})\s*[:\-]?\s*(.*?)(?=(?:{next_sections})\s*[:\-]|\Z)'
)


# =========================================================================
# GENERIC LABELED-FIELD FALLBACK
# =========================================================================

def generic_field_pattern(field_name_aliases, value_pattern=r'[^\n,;|]{2,80}'):
    """
    Build a fallback pattern string for ANY custom/user-defined field,
    given a list of alias labels (e.g. ["father name", "father's name"]).
    Used by extractor.py's generic extractor for fields with no
    dedicated pattern above.
    """
    return build_label_pattern(field_name_aliases, value_pattern)