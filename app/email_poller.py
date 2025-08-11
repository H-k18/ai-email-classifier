import imaplib
import email
from email.header import decode_header
import os
import json

EMAILS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'emails.json')

def get_decoded_text(part):
    """A robust function to decode email parts."""
    charset = part.get_content_charset()
    payload = part.get_payload(decode=True)
    if charset and payload:
        try:
            return payload.decode(charset, 'ignore')
        except (UnicodeDecodeError, LookupError):
            return payload.decode('latin-1', 'ignore')
    elif payload:
        try:
            return payload.decode('utf-8', 'ignore')
        except UnicodeDecodeError:
            return payload.decode('latin-1', 'ignore')
    return ""

def fetch_new_emails():
    """
    Connects to an IMAP email server, fetches unread emails,
    and adds them to the emails.json database.
    """
    IMAP_SERVER = "imap.gmail.com"
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASS = os.environ.get('EMAIL_PASS')

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials not set. Skipping email fetch.")
        return

    print("Checking for new emails...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, "(UNSEEN)")
        email_ids = messages[0].split()

        if not email_ids:
            print("No new emails found.")
            return

        print(f"Found {len(email_ids)} new emails.")
        
        with open(EMAILS_DB_PATH, 'r') as f:
            db_emails = json.load(f)
        
        max_id = max([e['id'] for e in db_emails]) if db_emails else 0
        newly_added_emails = 0

        for email_id in email_ids:
            # --- THIS IS THE FIX ---
            # Wrap each email in a try/except block to isolate errors.
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "latin-1", 'ignore')
                        
                        from_, encoding = decode_header(msg.get("From"))[0]
                        if isinstance(from_, bytes):
                            from_ = from_.decode(encoding if encoding else "latin-1", 'ignore')

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = get_decoded_text(part)
                                    break
                        else:
                            body = get_decoded_text(msg)
                        
                        max_id += 1
                        new_email = {
                            "id": max_id,
                            "from": from_,
                            "subject": subject,
                            "body": body,
                            "category": "primary"
                        }
                        db_emails.append(new_email)
                        newly_added_emails += 1
            except Exception as e:
                print(f"Could not process email ID {email_id.decode()}: {e}. Skipping.")
                continue # Move to the next email

        with open(EMAILS_DB_PATH, 'w') as f:
            json.dump(db_emails, f, indent=4)
        
        if newly_added_emails > 0:
            print(f"Successfully added {newly_added_emails} new emails to the database.")

    except Exception as e:
        print(f"Failed to fetch emails: {e}")
    finally:
        if 'mail' in locals() and mail.state == 'SELECTED':
            mail.close()
            mail.logout()