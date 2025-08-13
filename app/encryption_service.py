# app/encryption_service.py
from cryptography.fernet import Fernet
import os

# Load the secret key from the environment
FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError("FERNET_KEY not set in .env file!")

cipher_suite = Fernet(FERNET_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    if not data:
        return ""
    encrypted_text = cipher_suite.encrypt(data.encode())
    return encrypted_text.decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string."""
    if not encrypted_data:
        return ""
    try:
        decrypted_text = cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_text.decode()
    except Exception:
        # If decryption fails (e.g., invalid key or data), return an empty string
        return ""