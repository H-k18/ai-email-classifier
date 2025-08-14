import pytest
from app.utils.text_cleaner import clean_email_text
from app.encryption_service import encrypt_data, decrypt_data

# --- Unit Tests for the Text Cleaner ---

def test_clean_email_text_removes_headers():
    """Tests that the cleaner correctly extracts the body from a full raw email."""
    raw_email = """From: sender@example.com
Subject: Test
Content-Type: text/plain

This is the actual body of the email.
"""
    cleaned = clean_email_text(raw_email)
    assert cleaned == "actual body email"

def test_clean_email_text_handles_simple_string():
    """Tests that the cleaner works correctly on a simple string without headers."""
    raw_text = "Congratulations you have WON!"
    cleaned = clean_email_text(raw_text)
    assert cleaned == "congratulations won"

# --- Unit Tests for the Encryption Service ---

def test_encryption_decryption_cycle():
    """Tests that a string can be encrypted and then decrypted back to its original form."""
    original_text = "my-secret-16-digit-password"
    encrypted = encrypt_data(original_text)
    decrypted = decrypt_data(encrypted)

    assert encrypted != original_text
    assert decrypted == original_text

def test_decrypt_handles_invalid_data():
    """Tests that decryption returns an empty string for invalid or corrupted data."""
    invalid_encrypted_data = "this-is-not-valid-encrypted-data"
    decrypted = decrypt_data(invalid_encrypted_data)
    assert decrypted == ""