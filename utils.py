import re

def structure_extracted_data(text):
    data = {
        "dates": [],
        "amounts": [],
        "email": None,
        "raw_text": text
    }
    clean_text = text.replace("\n", " ")
    # Find dates (e.g., 12/31/2023 or 2023-12-31)
    date_pattern = r'\d{2,4}[-/]\d{2}[-/]\d{2,4}'
    data["dates"] = re.findall(date_pattern, text)
    
    # Find currency/amounts (e.g., $1,200.50 or 500.00)
    amount_pattern = r'[\$£€]?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))'
    data["amounts"] = re.findall(amount_pattern, text)
    
    # Find email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        data["email"] = email_match.group()
        
    return data