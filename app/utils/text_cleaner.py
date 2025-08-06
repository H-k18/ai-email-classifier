# app/utils/text_cleaner.py
import re
import email
from nltk.corpus import stopwords

def clean_email_text(raw_text: str) -> str:
    """
    Cleans email text for prediction. This version is robust and handles
    both full raw email source and simple text strings.

    Args:
        raw_text (str): The raw string content.

    Returns:
        str: The cleaned text, ready for vectorization.
    """
    if not isinstance(raw_text, str):
        return ""

    # --- This is the key change ---
    # We first try to parse it as a full email. If that fails or results
    # in an empty body, we fall back to treating the raw_text as the body.
    try:
        msg = email.message_from_string(raw_text)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # If parsing results in an empty body (like for a simple string), use the original text
        if not body.strip():
            body = raw_text

    except Exception:
        # If any parsing error occurs, assume the raw_text is the body
        body = raw_text

    # Continue with the cleaning process on the determined body text
    body = body.lower()
    body = re.sub(r'http\S+|www\S+|https\S+', '', body, flags=re.MULTILINE)
    body = re.sub(r'\S*@\S*\s?', '', body)
    body = re.sub(r'\d+', '', body)
    body = re.sub(r'[^\w\s]', '', body)
    body = re.sub(r'\s+', ' ', body).strip()
    
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in body.split() if word not in stop_words and len(word) > 2]
    
    return " ".join(tokens)
