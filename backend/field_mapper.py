"""
backend/field_mapper.py

Maps user-facing field names (and their aliases / OCR-friendly synonyms)
to the internal extractor functions in extractor.py.

This is the ONLY place that knows how a human-typed field name like
"Ph No", "Mobile Number", or "Contact" resolves to the `phones`
extractor. Adding support for a new field requires:

    1. Write one extractor function in extractor.py (if not already
       covered by extract_custom_field).
    2. Add ONE entry to FIELD_REGISTRY below.

parser.py never hardcodes field names — it only calls
`resolve_field(user_field_name)` and executes whatever it gets back.

CHANGELOG (OCR-tolerance refactor):
    - Purely additive alias entries for email, phone, github, and
      linkedin so that common OCR-mangled or casually-typed user
      input ("E-mail", "E Mail", "Git Hub", "Linked In", "Ph",
      "Contact Number:", etc.) resolves to the correct field.
      No keys, extractors, or dataclass shape changed. No aliases
      removed — only added.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from backend import extractor as ext


# =========================================================================
# FIELD DEFINITION
# =========================================================================

@dataclass(frozen=True)
class FieldDefinition:
    """
    key:        canonical internal field name (used as the JSON key
                in the response, and as the dict key in FIELD_REGISTRY)
    aliases:    all the ways a user might type this field, lowercase
    extractor:  callable(raw_text) -> value  (str | list | None)
                For fields with dedicated extractor functions.
    multi:      True if the field naturally returns a list of values
    """
    key: str
    aliases: List[str] = field(default_factory=list)
    extractor: Optional[Callable] = None
    multi: bool = False


# =========================================================================
# REGISTRY
#
# Order doesn't matter for lookup (alias index is built below), but
# keeping fields grouped by domain keeps this readable/maintainable.
# =========================================================================

FIELD_REGISTRY = {

    # ---- Identity ----
    "name": FieldDefinition(
        key="name",
        aliases=["name", "full name", "candidate name", "applicant name", "customer name"],
        extractor=ext.extract_name,
        multi=False,
    ),
    "names": FieldDefinition(
        key="names",
        aliases=["names", "all names"],
        extractor=ext.extract_names,
        multi=True,
    ),

    # ---- Contact ----
    "email": FieldDefinition(
        key="email",
        aliases=[
            "email", "email id", "email address", "e-mail", "mail id",
            # NEW: additional OCR/casual-typing variants
            "e mail", "e-mail id", "e mail id", "e-mail address",
            "e mail address", "mail", "mail address", "emailid",
        ],
        extractor=ext.extract_email,
        multi=False,
    ),
    "phone": FieldDefinition(
        key="phone",
        aliases=[
            "phone", "phones", "phone number", "mobile", "mobile number",
            "contact", "contact no", "contact number", "ph no", "tel",
            # NEW: additional OCR/casual-typing variants
            "ph", "ph.no", "ph. no", "phone no", "phone no.", "mob",
            "mob no", "mob. no", "mobile no", "cell", "cell number",
            "cell no", "whatsapp", "whatsapp number", "telephone",
            "telephone number", "contact number:", "contact:",
        ],
        extractor=ext.extract_phones,
        multi=True,
    ),
    "address": FieldDefinition(
        key="address",
        aliases=[
            "address", "residential address", "permanent address",
            "current address", "location",
        ],
        extractor=ext.extract_address,
        multi=False,
    ),

    # ---- Social / Web ----
    "github": FieldDefinition(
        key="github",
        aliases=[
            "github", "git hub", "github profile", "github url",
            # NEW: additional OCR/casual-typing variants
            "git-hub", "git_hub", "githubid", "github id",
            "github username", "github link",
        ],
        extractor=ext.extract_github,
        multi=True,
    ),
    "linkedin": FieldDefinition(
        key="linkedin",
        aliases=[
            "linkedin", "linked in", "linkedin profile", "linkedin url",
            # NEW: additional OCR/casual-typing variants
            "linked-in", "linked_in", "linkedinid", "linkedin id",
            "linkedin username", "linkedin link", "linked in profile",
        ],
        extractor=ext.extract_linkedin,
        multi=True,
    ),
    "portfolio": FieldDefinition(
        key="portfolio",
        aliases=["portfolio", "website", "personal website", "portfolio link"],
        extractor=ext.extract_portfolio,
        multi=True,
    ),

    # ---- Dates / Money ----
    "dates": FieldDefinition(
        key="dates",
        aliases=["dates", "date", "important dates"],
        extractor=ext.extract_dates,
        multi=True,
    ),
    "amount": FieldDefinition(
        key="amount",
        aliases=["amount", "amounts", "price", "cost"],
        extractor=ext.extract_amounts,
        multi=True,
    ),
    "total_amount": FieldDefinition(
        key="total_amount",
        aliases=[
            "total amount", "total", "grand total", "amount due",
            "balance due", "net payable",
        ],
        extractor=ext.extract_total_amount,
        multi=False,
    ),

    # ---- Indian Government IDs ----
    "pan": FieldDefinition(
        key="pan",
        aliases=["pan", "pan no", "pan number", "permanent account number"],
        extractor=ext.extract_pan,
        multi=False,
    ),
    "aadhar": FieldDefinition(
        key="aadhar",
        aliases=["aadhar", "aadhaar", "aadhar no", "aadhaar number", "uid", "uidai"],
        extractor=ext.extract_aadhar,
        multi=False,
    ),
    "gst": FieldDefinition(
        key="gst",
        aliases=["gst", "gstin", "gst no", "gst number"],
        extractor=ext.extract_gst,
        multi=False,
    ),
    "ifsc": FieldDefinition(
        key="ifsc",
        aliases=["ifsc", "ifsc code"],
        extractor=ext.extract_ifsc,
        multi=False,
    ),
    "account_number": FieldDefinition(
        key="account_number",
        aliases=["account number", "account no", "a/c no", "a/c number", "bank account"],
        extractor=ext.extract_account_number,
        multi=False,
    ),

    # ---- Invoice / Billing ----
    "invoice_number": FieldDefinition(
        key="invoice_number",
        aliases=[
            "invoice number", "invoice no", "invoice #", "inv no",
            "bill no", "bill number", "receipt no", "receipt number",
        ],
        extractor=ext.extract_invoice_number,
        multi=False,
    ),
    "pincode": FieldDefinition(
        key="pincode",
        aliases=["pincode", "pin code", "zip", "zip code", "postal code"],
        extractor=ext.extract_pincode,
        multi=False,
    ),

    # ---- Resume-style sections ----
    "company": FieldDefinition(
        key="company",
        aliases=["company", "organization", "organisation", "employer", "employer name"],
        extractor=ext.extract_company,
        multi=False,
    ),
    "skills": FieldDefinition(
        key="skills",
        aliases=["skills", "technical skills", "key skills", "core competencies"],
        extractor=ext.extract_skills,
        multi=True,
    ),
    "education": FieldDefinition(
        key="education",
        aliases=["education", "academic background", "qualification", "qualifications"],
        extractor=ext.extract_education,
        multi=False,
    ),
    "experience": FieldDefinition(
        key="experience",
        aliases=["experience", "work experience", "employment history", "professional experience"],
        extractor=ext.extract_experience,
        multi=False,
    ),
    "projects": FieldDefinition(
        key="projects",
        aliases=["projects", "academic projects", "personal projects"],
        extractor=ext.extract_projects,
        multi=False,
    ),
}


# =========================================================================
# ALIAS INDEX (built once at import time)
# =========================================================================

def _build_alias_index():
    index = {}
    for field_def in FIELD_REGISTRY.values():
        for alias in field_def.aliases:
            index[alias.strip().lower()] = field_def
        # canonical key itself is always a valid alias too
        index[field_def.key.strip().lower()] = field_def
    return index


_ALIAS_INDEX = _build_alias_index()


# =========================================================================
# PUBLIC API
# =========================================================================

def resolve_field(user_field_name):
    """
    Resolve a user-supplied field name string to its FieldDefinition.

    Returns:
        FieldDefinition if the field is known (has a dedicated
        extractor and/or aliases registered).
        None if the field is completely unknown -> caller (parser.py)
        should fall back to extract_custom_field() using the raw
        field name as its own alias.
    """
    if not user_field_name:
        return None
    return _ALIAS_INDEX.get(user_field_name.strip().lower())


def normalize_field_key(user_field_name):
    """
    Returns the canonical JSON key to use in the response for a given
    user-supplied field name — either the matched FieldDefinition's
    key, or a slugified version of the raw input for unknown/custom
    fields, so response keys stay stable and predictable.
    """
    resolved = resolve_field(user_field_name)
    if resolved:
        return resolved.key
    return (
        user_field_name.strip().lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def list_supported_fields():
    """Returns sorted list of all canonical field keys — useful for docs/UI."""
    return sorted(FIELD_REGISTRY.keys())