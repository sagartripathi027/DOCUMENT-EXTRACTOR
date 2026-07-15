import re

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
    "UNDERGRADUATE", "COMPUTER", "CBSE", "JBP", "LMS", "CGF", "CLASS"
}

EXCLUDE_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com",
    "icloud.com", "live.com", "protonmail.com", "yahoo.co.in", "aol.com"
}

TECH_TERM_DOMAINS = {
    "socket.io", "node.js", "vue.js", "react.js", "d3.js", "express.js",
    "next.js", "nuxt.js", "three.js", "chart.js", "ember.js", "backbone.js",
    "angular.js", "jquery.js", "webpack.js"
}

MONTHS = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)


def _fix_email_ocr(text):
    fixed = text
    fixed = re.sub(r'\s*@\s*', '@', fixed)
    fixed = re.sub(r'\s*\.\s*(com|in|org|net|co|edu|io)\b', r'.\1', fixed, flags=re.IGNORECASE)
    fixed = re.sub(
        r'@\s*(gmail|yahoo|outlook|hotmail|rediffmail|icloud)\s*(?:\.|,)?\s*(com|in|co\.in|net)\b',
        r'@\1.\2', fixed, flags=re.IGNORECASE
    )
    fixed = re.sub(
        r'([a-zA-Z0-9._%+-]+)\s*\(?\bat\b\)?\s*(gmail|yahoo|outlook|hotmail|rediffmail|icloud)\s*\(?\bdot\b\)?\s*(com|in|co\.in|net)',
        r'\1@\2.\3', fixed, flags=re.IGNORECASE
    )
    fixed = re.sub(
        r'([a-zA-Z0-9._%+-]+)@(gmail|yahoo|outlook|hotmail|rediffmail|icloud)(com|in|net)\b',
        r'\1@\2.\3', fixed, flags=re.IGNORECASE
    )
    return fixed


def _is_valid_name_token(word):
    w = word.strip().upper()
    if not w or w in IGNORE_WORDS:
        return False
    if len(w) < 2:
        return False
    if any(ch.isdigit() for ch in w):
        return False
    return True


def _extract_names(text):
    candidates = []

    caps_pattern = r'\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,3}\b'
    for m in re.finditer(caps_pattern, text):
        words = m.group().split()
        if all(_is_valid_name_token(w) for w in words) and any(len(w) > 2 for w in words):
            candidates.append((m.start(), " ".join(w.title() for w in words)))

    title_pattern = r'(?:Name[:\-]\s*)?\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
    for m in re.finditer(title_pattern, text):
        words = m.group().split()
        if all(_is_valid_name_token(w) for w in words):
            candidates.append((m.start(), re.sub(r'\s+', ' ', m.group()).strip()))

    candidates.sort(key=lambda x: x[0])

    seen = set()
    result = []
    for _, c in candidates:
        key = c.upper()
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def _extract_github(text):
    results = []

    url_pattern = r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)?)'
    for m in re.finditer(url_pattern, text, re.IGNORECASE):
        results.append(f"github.com/{m.group(1)}")

    label_pattern = r'\bgithub\b\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9_-]{1,38})'
    for m in re.finditer(label_pattern, text, re.IGNORECASE):
        username = m.group(1)
        if username.lower() in ("com", "in", "io") or "@" in username:
            continue
        results.append(f"github.com/{username}")

    return list(dict.fromkeys(results))


def _extract_linkedin(text):
    results = []

    url_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/([A-Za-z0-9_-]+)/?'
    for m in re.finditer(url_pattern, text, re.IGNORECASE):
        results.append(f"linkedin.com/in/{m.group(1)}")

    label_pattern = r'\blinkedin\b\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9_-]{1,38})'
    for m in re.finditer(label_pattern, text, re.IGNORECASE):
        username = m.group(1)
        if username.lower() in ("com", "in", "io") or "@" in username:
            continue
        results.append(f"linkedin.com/in/{username}")

    return list(dict.fromkeys(results))


def parse_structured_data(text):
    data = {
        "dates": [],
        "amounts": [],
        "email": None,
        "phones": [],
        "github": [],
        "linkedin": [],
        "portfolio": [],
        "names": [],
        "raw_text": text
    }

    norm = re.sub(r'[ \t]+', ' ', text)
    norm = re.sub(r'\s*\n\s*', ' ', norm)
    norm = re.sub(r'\s+', ' ', norm).strip()

    clean = norm.lower()
    clean = re.sub(r'[^a-z0-9@.$:/\- ]', ' ', clean)

    # ------------------ DATE ------------------
    date_patterns = [
        r'\d{4}[-/]\d{2}[-/]\d{2}',
        r'\d{2}[-/]\d{2}[-/]\d{4}',
        r'\b\d{8}\b',
        rf'\b(?:{MONTHS})[a-zA-Z]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b',
        rf'\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})[a-zA-Z]*\.?,?\s+\d{{4}}\b',
        rf'\b(?:{MONTHS})[a-zA-Z]*\.?\s+\d{{4}}\b',
        r'\b\d{4}\s*-\s*\d{4}\b'
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, norm, re.IGNORECASE)
        data["dates"].extend(matches)

    for pattern in [r'\d{4}[-/]\d{2}[-/]\d{2}', r'\d{2}[-/]\d{2}[-/]\d{4}', r'\b\d{8}\b']:
        data["dates"].extend(re.findall(pattern, clean))

    data["dates"] = list(dict.fromkeys(d.strip() for d in data["dates"]))

    # ------------------ AMOUNT ------------------
    amount_pattern = r'(?:₹|Rs\.?\s?|INR\s?|\$|€)\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?'
    old_amount_pattern = r'\d{3,}(?:[.,]\d{2})'

    amounts = re.findall(amount_pattern, norm)
    amounts.extend(re.findall(old_amount_pattern, clean))
    data["amounts"] = list(dict.fromkeys(a.strip() for a in amounts))

    # ------------------ EMAIL ------------------
    email_source = _fix_email_ocr(norm)
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, email_source)

    if match:
        data["email"] = match.group().lower()
    else:
        fallback = re.search(email_pattern, clean)
        if fallback:
            data["email"] = fallback.group()

    # ------------------ PHONE ------------------
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{2,5}\)[-.\s]?)?\d{3,5}[-.\s]?\d{3,4}(?:[-.\s]?\d{2,4})?'
    phone_candidates = re.findall(phone_pattern, norm)
    phones = []
    for p in phone_candidates:
        digits = re.sub(r'\D', '', p)
        if 7 <= len(digits) <= 15:
            phones.append(p.strip())
    data["phones"] = list(dict.fromkeys(phones))

    # ------------------ GITHUB / LINKEDIN ------------------
    data["github"] = _extract_github(norm)
    data["linkedin"] = _extract_linkedin(norm)

    # ------------------ PORTFOLIO ------------------
    url_pattern = r'(?:https?://)?(?:www\.)?[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?'
    all_urls = re.findall(url_pattern, norm, re.IGNORECASE)

    email_domain = data["email"].split('@')[1].lower() if data["email"] else None

    portfolio = []
    for u in all_urls:
        u_lower = u.lower().rstrip('.,')
        domain = u_lower.split('/')[0]

        if 'github.com' in u_lower or 'linkedin.com' in u_lower:
            continue
        if '@' in u:
            continue
        if domain in EXCLUDE_DOMAINS or domain in TECH_TERM_DOMAINS:
            continue
        if email_domain and domain == email_domain:
            continue
        if not re.search(r'\.(com|in|io|dev|me|org|net|co|app)\b', domain):
            continue

        portfolio.append(u)

    data["portfolio"] = list(dict.fromkeys(portfolio))

    # ------------------ NAME ------------------
    data["names"] = _extract_names(norm)

    return data