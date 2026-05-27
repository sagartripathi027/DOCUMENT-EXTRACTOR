import re

def parse_structured_data(text):
    data = {
        "dates": [],
        "amounts": [],
        "email": None,
        "raw_text": text
    }

    # 🔹 CLEAN TEXT (important)
    clean = text.lower()
    clean = re.sub(r'[^a-z0-9@.$:/\- ]', ' ', clean)

    # DATE
    # Matches:
    # 2023-12-01, 12/15/2023, 20231201
    date_patterns = [
        r'\d{4}[-/]\d{2}[-/]\d{2}',
        r'\d{2}[-/]\d{2}[-/]\d{4}',
        r'\b\d{8}\b'  # 20231201
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, clean)
        data["dates"].extend(matches)

    # AMOUNT
    amount_pattern = r'\d{3,}(?:[.,]\d{2})'
    data["amounts"] = re.findall(amount_pattern, clean)

    # EMAIL
    # flexible email detection
    email_pattern = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
    match = re.search(email_pattern, clean)

    if match:
        data["email"] = match.group()

    return data
