# app/utils/text_cleaner.py
import re
import email
from nltk.corpus import stopwords

def clean_email_text(raw_email: str) -> str:
    """
    Cleans the raw text of an email by removing headers, footers, and special characters.
    This function is designed to be used for inference.

    Args:
        raw_email (str): The raw string content of an email.

    Returns:
        str: The cleaned email body text, ready for vectorization.
    """
    if not isinstance(raw_email, str):
        return ""

    msg = email.message_from_string(raw_email)
    
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    continue
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = msg.get_payload()

    body = body.lower()
    body = re.sub(r'http\S+|www\S+|https\S+', '', body, flags=re.MULTILINE)
    body = re.sub(r'\S*@\S*\s?', '', body)
    body = re.sub(r'\d+', '', body)
    body = re.sub(r'[^\w\s]', '', body)
    body = re.sub(r'\s+', ' ', body).strip()
    
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in body.split() if word not in stop_words and len(word) > 2]
    
    return " ".join(tokens)