# app/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify
from app.ml_service.model_provider import predictor_instance
import json
import os

main_bp = Blueprint('main_bp', __name__)

# Path to our new JSON database
EMAILS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '/home/ubantu/Documents/MNIT5001/ai-email-classifier/emails.json')

def read_emails():
    """Helper function to read emails from the JSON file."""
    with open(EMAILS_DB_PATH, 'r') as f:
        return json.load(f)

def write_emails(emails):
    """Helper function to write emails back to the JSON file."""
    with open(EMAILS_DB_PATH, 'w') as f:
        json.dump(emails, f, indent=4)

@main_bp.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@main_bp.route('/get_emails', methods=['GET'])
def get_emails():
    """API endpoint to fetch all emails from our JSON database."""
    emails = read_emails()
    return jsonify(emails)

@main_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    email_text = data['email_text']
    prediction = predictor_instance.predict(email_text)
    return jsonify({'prediction': prediction})

@main_bp.route('/learn', methods=['POST'])
def learn():
    data = request.get_json()
    email_id = data['email_id']
    email_text = data['email_text']
    correct_label = data['correct_label']
    
    # 1. Teach the in-memory AI model
    predictor_instance.learn(email_text, correct_label)
    
    # 2. Update the permanent database
    emails = read_emails()
    for email in emails:
        if email['id'] == email_id:
            email['category'] = correct_label
            break
    write_emails(emails)
    
    return jsonify({'message': f"Model updated and correction saved permanently."})

@main_bp.route('/get_categories', methods=['GET'])
def get_categories():
    categories = predictor_instance.get_known_categories()
    return jsonify({'categories': categories})