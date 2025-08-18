# app/utils/text_cleaner.py
import re
import email
from nltk.corpus import stopwords

def clean_email_text(raw_email: str) -> str:
    """
    Cleans email text for prediction. This version is robust and handles
    both full raw email source and simple text strings.
    """
    if not isinstance(raw_email, str):
        return ""

    try:
        msg = email.message_from_string(raw_email)
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
        
        if not body.strip():
            body = raw_email

    except Exception:
        # --- THIS IS THE FIX ---
        # The variable name was incorrect. It should be raw_email.
        body = raw_email

    # Continue with the cleaning process on the determined body text
    body = body.lower()
    body = re.sub(r'http\S+|www\S+|https\S+', '', body, flags=re.MULTILINE)
    body = re.sub(r'\S*@\S*\s?', '', body)
    body = re.sub(r'\d+', '', body)
    body = re.sub(r'[^\w\s]', '', body)
    body = re.sub(r'\s+', ' ', body).strip()
    
    stop_words = set(stopwords.words('english'))
    words_to_keep = {'won', 'not', 'no', 'win'}
    stop_words = stop_words - words_to_keep
    
    tokens = [word for word in body.split() if word not in stop_words and len(word) > 2]
    
    return " ".join(tokens)