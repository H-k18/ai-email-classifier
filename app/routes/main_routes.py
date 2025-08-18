
# app/routes/main_routes.py
from flask import Blueprint, render_template, request, jsonify, Response # <-- THIS LINE IS FIXED
from flask_login import login_required, current_user
from app.ml_service.model_provider import predictor_instance
from app.models import User, Email, Category
from app import db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import os

main_bp = Blueprint('main_bp', __name__)




@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/get_emails', methods=['GET'])
@login_required
def get_emails():
    user_emails = Email.query.options(joinedload(Email.category)).filter_by(user_id=current_user.id).all()
    emails_list = [
        {"id": email.id, "from": email.sender, "subject": email.subject, "body": email.body, "category": email.category.name}
        for email in user_emails
    ]
    return jsonify(emails_list)

# --- THIS IS THE NEW DEDICATED ROUTE FOR EMAIL CONTENT ---
@main_bp.route('/email_content/<int:email_id>')
@login_required
def email_content(email_id):
    """Securely serves the raw HTML content of a single email."""
    email = db.session.get(Email, email_id)
    if not email or email.user_id != current_user.id:
        return "Not found", 404
    return Response(email.body, mimetype='text/html')

@main_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """
    This now correctly predicts using the AI model's text cleaner
    to avoid the "ERROR" bug.
    """
    data = request.get_json()
    # Use the predictor's own internal cleaner
    prediction = predictor_instance.predict(data['email_text'])
    return jsonify({'prediction': prediction})

@main_bp.route('/learn', methods=['POST'])
@login_required
def learn():
    data = request.get_json()
    email_id = data['email_id']
    correct_label = data['correct_label']
    
    predictor_instance.learn(data['email_text'], correct_label)
    
    category = Category.query.filter_by(name=correct_label, user_id=current_user.id).first()
    if not category:
        category = Category(name=correct_label, owner=current_user)
        db.session.add(category)
        db.session.commit()

    email_to_update = db.session.get(Email, email_id)
    if email_to_update and email_to_update.user_id == current_user.id:
        email_to_update.category_id = category.id
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

    category_to_delete = Category.query.filter_by(name=category_to_delete_name, user_id=current_user.id).first()
    
    if category_to_delete:
        primary_category = Category.query.filter_by(name='primary', user_id=current_user.id).first()
        Email.query.filter_by(category_id=category_to_delete.id).update({'category_id': primary_category.id})
        db.session.delete(category_to_delete)
        db.session.commit()
        return jsonify({'message': f"Category '{category_to_delete_name}' deleted."})
    
    return jsonify({'error': 'Category not found.'}), 404


@main_bp.route('/search', methods=['GET'])
@login_required
def search_emails():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    search_term = f"%{query}%"
    user_emails = Email.query.options(joinedload(Email.category)).filter(
        Email.user_id == current_user.id,
        or_(
            Email.sender.ilike(search_term),
            Email.subject.ilike(search_term),
            Email.body.ilike(search_term)
        )
    ).all()

    emails_list = [
        {"id": email.id, "from": email.sender, "subject": email.subject, "body": email.body, "category": email.category.name}
        for email in user_emails
    ]
    return jsonify(emails_list)

@main_bp.route('/refresh_emails', methods=['POST'])
@login_required
def refresh_emails():
    from app.email_poller import fetch_emails_for_user
    user = db.session.get(User, current_user.id)
    success = fetch_emails_for_user(user)
    if success:
        return jsonify({'message': 'Email check complete.'})
    else:
        return jsonify({'error': 'Failed to fetch emails.'}), 500

@main_bp.route('/bulk_update', methods=['POST'])
@login_required
def bulk_update():
    data = request.get_json()
    email_ids = data.get('email_ids', [])
    target_category_name = data.get('category')

    if not email_ids or not target_category_name:
        return jsonify({'error': 'Missing email IDs or category'}), 400

    target_category = Category.query.filter_by(name=target_category_name, user_id=current_user.id).first()
    if not target_category:
        return jsonify({'error': 'Category not found'}), 404

    Email.query.filter(
        Email.id.in_(email_ids),
        Email.user_id == current_user.id
    ).update({'category_id': target_category.id}, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({'message': f'Successfully moved {len(email_ids)} emails.'})