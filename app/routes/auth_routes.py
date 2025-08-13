# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import mail, db
from app.models import User, Category
import random
from app.encryption_service import encrypt_data, decrypt_data

auth_bp = Blueprint('auth_bp', __name__)

# --- LOGIN ROUTES ---
@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth_bp.login'))

    login_user(user)
    return redirect(url_for('main_bp.index'))

# --- SIGNUP ROUTES ---
@auth_bp.route('/signup')
def signup():
    return render_template('signup.html')

@auth_bp.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user:
        flash('Email address already registered.')
        return redirect(url_for('auth_bp.signup'))

    otp = random.randint(100000, 999999)
    session['otp'] = otp
    session['user_details'] = {
        "username": username,
        "password": generate_password_hash(password, method='pbkdf2:sha256')
    }

    try:
        msg = Message('Your Verification Code', recipients=[username])
        msg.body = f'Your verification code for AI Email Classifier is: {otp}'
        mail.send(msg)
        flash('A verification code has been sent to your email.')
        return redirect(url_for('auth_bp.verify'))
    except Exception as e:
        flash(f'Could not send email. Please try again. Error: {e}')
        return redirect(url_for('auth_bp.signup'))

# --- VERIFICATION ROUTES ---
@auth_bp.route('/verify')
def verify():
    return render_template('verify.html')

@auth_bp.route('/verify', methods=['POST'])
def verify_post():
    submitted_otp = request.form.get('otp')
    if 'otp' in session and submitted_otp == str(session['otp']):
        user_details = session.pop('user_details', None)
        session.pop('otp', None)

        # Create the new user in the database
        new_user = User(
            username=user_details['username'],
            password=user_details['password']
        )
        db.session.add(new_user)
        db.session.commit() # Commit to get the new_user.id

        # Create default categories for the new user
        primary_cat = Category(name='primary', owner=new_user)
        spam_cat = Category(name='spam', owner=new_user)
        db.session.add(primary_cat)
        db.session.add(spam_cat)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('auth_bp.login'))
    else:
        flash('Invalid verification code. Please try again.')
        return redirect(url_for('auth_bp.verify'))

# --- LOGOUT ROUTE ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))

# --- SETTINGS ROUTES ---
@auth_bp.route('/settings')
@login_required
def settings():
    saved_email = decrypt_data(current_user.encrypted_email or "")
    email_address_to_display = saved_email if saved_email else current_user.username
    email_settings = {
        "imap_server": current_user.imap_server or "imap.gmail.com",
        "email_address": email_address_to_display
    }
    return render_template('settings.html', settings=email_settings)

@auth_bp.route('/settings', methods=['POST'])
@login_required
def settings_post():
    form_action = request.form.get('action')
    user = User.query.get(current_user.id)

    if form_action == 'update_email':
        user.imap_server = request.form.get('imap_server')
        user.encrypted_email = encrypt_data(request.form.get('email_address'))
        app_password = request.form.get('app_password')
        if app_password:
            user.encrypted_password = encrypt_data(app_password)
        flash('Your email settings have been saved successfully.')

    elif form_action == 'change_password':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect.')
        elif new_password != confirm_password:
            flash('New passwords do not match.')
        else:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            flash('Your password has been changed successfully.')

    db.session.commit()
    return redirect(url_for('auth_bp.settings'))