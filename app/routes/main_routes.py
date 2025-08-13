# app/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.ml_service.model_provider import predictor_instance
from app.models import Email, Category
from app import db

main_bp = Blueprint('main_bp', __name__)

# --- MAIN ROUTES (Now User-Aware) ---
@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/get_emails', methods=['GET'])
@login_required
def get_emails():
    user_emails = Email.query.filter_by(user_id=current_user.id).all()
    emails_list = [
        {
            "id": email.id,
            "from": email.sender,
            "subject": email.subject,
            "body": email.body,
            "category": email.category.name
        } for email in user_emails
    ]
    return jsonify(emails_list)

@main_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.get_json()
    prediction = predictor_instance.predict(data['email_text'])
    return jsonify({'prediction': prediction})

@main_bp.route('/learn', methods=['POST'])
@login_required
def learn():
    data = request.get_json()
    email_id = data['email_id']
    correct_label = data['correct_label']
    
    predictor_instance.learn(data['email_text'], correct_label)
    
    # Find or create the category for the current user
    category = Category.query.filter_by(name=correct_label, user_id=current_user.id).first()
    if not category:
        category = Category(name=correct_label, owner=current_user)
        db.session.add(category)
        db.session.commit()

    # Update the email's category
    email = Email.query.get(email_id)
    if email and email.user_id == current_user.id:
        email.category_id = category.id
        db.session.commit()
    
    return jsonify({'message': f"Model updated and correction saved permanently."})

@main_bp.route('/get_categories', methods=['GET'])
@login_required
def get_categories():
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify({'categories': [cat.name for cat in user_categories]})

@main_bp.route('/delete_category', methods=['POST'])
@login_required
def delete_category():
    data = request.get_json()
    category_to_delete_name = data['category']

    if category_to_delete_name in ['primary', 'spam']:
        return jsonify({'error': 'Cannot delete core folders.'}), 400

    # Find the category to delete
    category_to_delete = Category.query.filter_by(name=category_to_delete_name, user_id=current_user.id).first()
    
    if category_to_delete:
        # Find the user's primary category
        primary_category = Category.query.filter_by(name='primary', user_id=current_user.id).first()
        
        # Re-assign emails to the primary category
        Email.query.filter_by(category_id=category_to_delete.id).update({'category_id': primary_category.id})
        
        # Delete the category
        db.session.delete(category_to_delete)
        db.session.commit()
        return jsonify({'message': f"Category '{category_to_delete_name}' deleted."})
    
    return jsonify({'error': 'Category not found.'}), 404