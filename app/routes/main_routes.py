# app/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user # Import current_user
from app.ml_service.model_provider import predictor_instance
import json
import os

main_bp = Blueprint('main_bp', __name__)

# --- DATABASE FILE PATHS ---
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
EMAILS_DB_PATH = os.path.join(BASE_DIR, 'emails.json')
CATEGORIES_DB_PATH = os.path.join(BASE_DIR, 'categories.json')

# --- ROBUST HELPER FUNCTIONS ---
def read_json(path, default_data):
    """Reads a JSON file. If it doesn't exist, creates it with default data."""
    if not os.path.exists(path):
        write_json(path, default_data)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is empty or corrupted, return default data
        return default_data

def write_json(path, data):
    """Writes data to a JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# --- MAIN ROUTES ---
@main_bp.route('/')
@login_required  # --- THIS IS THE FIX --- This line protects the page
def index():
    return render_template('index.html', user = current_user)

@main_bp.route('/get_emails', methods=['GET'])
@login_required # Also protect API routes
def get_emails():
    # Provide default email data if the file is missing
    default_emails = [
        { "id": 1, "from": "Google", "subject": "Security alert", "body": "A new sign-in was detected.", "category": "primary" },
        { "id": 2, "from": "Promotions", "subject": "50% off all items!", "body": "Don't miss out on our biggest sale!", "category": "spam" }
    ]
    emails = read_json(EMAILS_DB_PATH, default_emails)
    return jsonify(emails)

@main_bp.route('/predict', methods=['POST'])
@login_required # Also protect API routes
def predict():
    data = request.get_json()
    prediction = predictor_instance.predict(data['email_text'])
    return jsonify({'prediction': prediction})

@main_bp.route('/learn', methods=['POST'])
@login_required # Also protect API routes
def learn():
    data = request.get_json()
    email_id = data['email_id']
    correct_label = data['correct_label']
    
    predictor_instance.learn(data['email_text'], correct_label)
    
    emails = read_json(EMAILS_DB_PATH, [])
    for email in emails:
        if email['id'] == email_id:
            email['category'] = correct_label
            break
    write_json(EMAILS_DB_PATH, emails)

    categories = read_json(CATEGORIES_DB_PATH, [])
    if correct_label not in categories:
        categories.append(correct_label)
        write_json(CATEGORIES_DB_PATH, categories)
    
    return jsonify({'message': f"Model updated and correction saved permanently."})

@main_bp.route('/get_categories', methods=['GET'])
@login_required # Also protect API routes
def get_categories():
    default_categories = ["primary", "spam"]
    categories = read_json(CATEGORIES_DB_PATH, default_categories)
    return jsonify({'categories': categories})

@main_bp.route('/delete_category', methods=['POST'])
@login_required # Also protect API routes
def delete_category():
    data = request.get_json()
    category_to_delete = data['category']

    if category_to_delete in ['primary', 'spam']:
        return jsonify({'error': 'Cannot delete core folders.'}), 400

    categories = read_json(CATEGORIES_DB_PATH, [])
    if category_to_delete in categories:
        categories.remove(category_to_delete)
        write_json(CATEGORIES_DB_PATH, categories)

    emails = read_json(EMAILS_DB_PATH, [])
    for email in emails:
        if email['category'] == category_to_delete:
            email['category'] = 'primary'
    write_json(EMAILS_DB_PATH, emails)
    
    return jsonify({'message': f"Category '{category_to_delete}' deleted."})