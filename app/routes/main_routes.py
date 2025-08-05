# app/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify, current_app

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@main_bp.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint to make a prediction.
    """
    data = request.get_json()
    if not data or 'email_text' not in data:
        return jsonify({'error': 'Missing email_text in request'}), 400

    email_text = data['email_text']
    
    prediction = current_app.predictor_service.predict(email_text)
    
    return jsonify({'prediction': prediction})