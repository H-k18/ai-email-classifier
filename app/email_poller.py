# app/email_poller.py
import imaplib
import email
from email.header import decode_header
import os
from app import create_app, db
from app.models import User, Email, Category
from app.encryption_service import decrypt_data

def get_decoded_text(part):
    """A robust function to decode email parts."""
    charset = part.get_content_charset() or 'utf-8'
    payload = part.get_payload(decode=True)
    try:
        return payload.decode(charset, 'ignore')
    except (UnicodeDecodeError, LookupError):
        return payload.decode('latin-1', 'ignore')

def fetch_emails_for_user(user):
    """
    Fetches new emails for a SINGLE user, prioritizing HTML content for correct formatting.
    """
    print(f"Checking for new emails for user: {user.username}")
    mail = None
    try:
        imap_server = user.imap_server
        email_user = decrypt_data(user.encrypted_email)
        email_pass = decrypt_data(user.encrypted_password)

        if not all([imap_server, email_user, email_pass]): return False

        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        is_new_user = Email.query.filter_by(user_id=user.id).count() == 0
        search_criteria = "ALL" if is_new_user else "(UNSEEN)"
        if is_new_user: print(f"New user detected. Performing initial sync...")

        status, messages = mail.search(None, search_criteria)
        email_ids = messages[0].split()

        if is_new_user and len(email_ids) > 250:
            email_ids = email_ids[-250:]

        if not email_ids:
            print(f"No new emails found for {user.username}.")
            return True

        print(f"Found {len(email_ids)} emails to process for {user.username}.")
        primary_category = Category.query.filter_by(name='primary', user_id=user.id).first()
        if not primary_category: return False

        batch_size = 20
        for i in range(0, len(email_ids), batch_size):
            batch = email_ids[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}...")
            for email_id in batch:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject_header = decode_header(msg["Subject"])
                            subject = subject_header[0][0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(subject_header[0][1] or 'utf-8', 'ignore')
                            
                            from_header = decode_header(msg.get("From"))
                            sender = from_header[0][0]
                            if isinstance(sender, bytes):
                                sender = sender.decode(from_header[0][1] or 'utf-8', 'ignore')
                            
                            html_body = ""
                            plain_body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/html" and not html_body:
                                        html_body = get_decoded_text(part)
                                    elif content_type == "text/plain" and not plain_body:
                                        plain_body = get_decoded_text(part)
                            else:
                                plain_body = get_decoded_text(msg)

                            # --- THIS IS THE DEFINITIVE FIX ---
                            # Prioritize the full HTML body. If it doesn't exist,
                            # fall back to the plain text, converting its line breaks to <br> tags.
                            body = html_body if html_body else plain_body.replace('\n', '<br>')
                            
                            new_email = Email(sender=sender, subject=subject, body=body, owner=user, category=primary_category)
                            db.session.add(new_email)
                except Exception as e:
                    print(f"Could not process email ID {email_id.decode()}: {e}. Skipping.")
                    continue
            db.session.commit()
            print(f"Batch {i//batch_size + 1} committed.")
        return True
    except Exception as e:
        print(f"Failed to fetch emails for user {user.username}: {e}")
        return False
    finally:
        if mail and mail.state == 'SELECTED':
            mail.close()
            mail.logout()

def poll_all_users():
    app = create_app()
    with app.app_context():
        users_to_poll = User.query.filter(User.encrypted_password != None).all()
        for user in users_to_poll:
            fetch_emails_for_user(user)