# app/config.py
import os

# Get the absolute path of the directory where this file is located
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration settings."""
    # Define paths for the machine learning models
    CLASSIFIER_MODEL_PATH = os.path.join(BASE_DIR, '..', '/home/mnit2024/Documents/emailclassifierApplication/email_classifier.joblib')
    VECTORIZER_MODEL_PATH = os.path.join(BASE_DIR, '..', '/home/mnit2024/Documents/emailclassifierApplication/vectorizer.joblib')