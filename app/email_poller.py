import imaplib
import email
from email.header import decode_header
import os
from app import create_app, db
from app.models import User, Email, Category
from app.encryption_service import decrypt_data

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
    Fetches new emails for ALL users who have provided credentials
    and saves them to the database.
    """
    app = create_app()
    with app.app_context():
        # Find all users who have saved their email credentials
        users_to_poll = User.query.filter(User.encrypted_password != None).all()
        
        if not users_to_poll:
            print("No users with polling credentials configured. Skipping email fetch.")
            return

        print(f"Polling emails for {len(users_to_poll)} user(s)...")

        for user in users_to_poll:
            print(f"Checking for new emails for user: {user.username}")
            try:
                # Decrypt the user's credentials
                imap_server = user.imap_server
                email_user = decrypt_data(user.encrypted_email)
                email_pass = decrypt_data(user.encrypted_password)

                if not imap_server or not email_user or not email_pass:
                    continue

                mail = imaplib.IMAP4_SSL(imap_server)
                mail.login(email_user, email_pass)
                mail.select("inbox")

                status, messages = mail.search(None, "(UNSEEN)")
                email_ids = messages[0].split()

                if not email_ids:
                    print(f"No new emails found for {user.username}.")
                    continue

                print(f"Found {len(email_ids)} new emails for {user.username}.")
                
                # Get the user's default 'primary' category
                primary_category = Category.query.filter_by(name='primary', user_id=user.id).first()
                if not primary_category:
                    print(f"Could not find a primary category for {user.username}. Skipping.")
                    continue

                for email_id in email_ids:
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
                                
                                # Create a new Email object and save it to the database
                                new_email = Email(
                                    sender=from_,
                                    subject=subject,
                                    body=body,
                                    owner=user,
                                    category=primary_category
                                )
                                db.session.add(new_email)
                    except Exception as e:
                        print(f"Could not process email ID {email_id.decode()} for user {user.username}: {e}. Skipping.")
                        continue
                
                db.session.commit()
                print(f"Successfully added {len(email_ids)} new emails for {user.username}.")

            except Exception as e:
                print(f"Failed to fetch emails for user {user.username}: {e}")
            finally:
                if 'mail' in locals() and mail.state == 'SELECTED':
                    mail.close()
                    mail.logout()