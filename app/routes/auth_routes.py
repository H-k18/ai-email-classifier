# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
# --- THIS IS THE FIX --- Import current_user
from flask_login import login_user, logout_user, login_required, current_user 
from flask_mail import Message
from app import mail
from app.user_model import User
import json
import os
import random
from app.encryption_service import encrypt_data, decrypt_data

auth_bp = Blueprint('auth_bp', __name__)

# --- DATABASE FILE PATHS ---
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
USERS_DB_PATH = os.path.join(BASE_DIR, 'users.json')

# --- LOGIN ROUTES (No changes) ---
@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    with open(USERS_DB_PATH, 'r') as f: users = json.load(f)
    user_data = next((user for user in users if user['username'] == username), None)
    if not user_data or not check_password_hash(user_data['password'], password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth_bp.login'))
    user = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password'])
    login_user(user)
    return redirect(url_for('main_bp.index'))

# --- SIGNUP ROUTES (Updated for OTP) ---
@auth_bp.route('/signup')
def signup():
    return render_template('signup.html')

@auth_bp.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username') # This will be the user's email
    password = request.form.get('password')

    with open(USERS_DB_PATH, 'r') as f: users = json.load(f)
    if any(user['username'] == username for user in users):
        flash('Email address already registered.')
        return redirect(url_for('auth_bp.signup'))

    # Generate OTP and store user info temporarily in the session
    otp = random.randint(100000, 999999)
    session['otp'] = otp
    session['user_details'] = {
        "username": username,
        "password": generate_password_hash(password, method='pbkdf2:sha256')
    }

    # Send the OTP email
    try:
        msg = Message('Your Verification Code', recipients=[username])
        msg.body = f'Your verification code for AI Email Classifier is: {otp}'
        mail.send(msg)
        flash('A verification code has been sent to your email.')
        return redirect(url_for('auth_bp.verify'))
    except Exception as e:
        flash(f'Could not send email. Please try again. Error: {e}')
        return redirect(url_for('auth_bp.signup'))

# --- NEW VERIFICATION ROUTES ---
@auth_bp.route('/verify')
def verify():
    return render_template('verify.html')

@auth_bp.route('/verify', methods=['POST'])
def verify_post():
    submitted_otp = request.form.get('otp')
    if 'otp' in session and submitted_otp == str(session['otp']):
        # OTP is correct, create the user account permanently
        user_details = session['user_details']
        with open(USERS_DB_PATH, 'r') as f: users = json.load(f)
        
        new_user = {
            "id": len(users) + 1,
            "username": user_details['username'],
            "password": user_details['password']
        }
        users.append(new_user)

        with open(USERS_DB_PATH, 'w') as f: json.dump(users, f, indent=4)

        # Clear the temporary data from the session
        session.pop('otp', None)
        session.pop('user_details', None)
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('auth_bp.login'))
    else:
        flash('Invalid verification code. Please try again.')
        return redirect(url_for('auth_bp.verify'))

# --- LOGOUT ROUTE (No changes) ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))
from app.encryption_service import encrypt_data, decrypt_data # Import encryption functions

# --- SETTINGS ROUTES ---
@auth_bp.route('/settings')
@login_required
def settings():
    with open(USERS_DB_PATH, 'r') as f:
        users = json.load(f)
    
    user_data = next((user for user in users if user['id'] == current_user.id), None)
    
    saved_email = decrypt_data(user_data.get("encrypted_email", ""))
    email_address_to_display = saved_email if saved_email else current_user.username

    email_settings = {
        "imap_server": user_data.get("imap_server", "imap.gmail.com"),
        "email_address": email_address_to_display
    }
    return render_template('settings.html', settings=email_settings)

@auth_bp.route('/settings', methods=['POST'])
@login_required
def settings_post():
    # --- THIS IS THE UPDATED LOGIC ---
    form_action = request.form.get('action')
    
    with open(USERS_DB_PATH, 'r') as f:
        users = json.load(f)
    
    user_data = next((user for user in users if user['id'] == current_user.id), None)

    if form_action == 'update_email':
        user_data['imap_server'] = request.form.get('imap_server')
        user_data['encrypted_email'] = encrypt_data(request.form.get('email_address'))
        app_password = request.form.get('app_password')
        if app_password:
            user_data['encrypted_password'] = encrypt_data(app_password)
        flash('Your email settings have been saved successfully.')

    elif form_action == 'change_password':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(user_data['password'], current_password):
            flash('Current password is incorrect.')
        elif new_password != confirm_password:
            flash('New passwords do not match.')
        else:
            user_data['password'] = generate_password_hash(new_password, method='pbkdf2:sha256')
            flash('Your password has been changed successfully.')

    with open(USERS_DB_PATH, 'w') as f:
        json.dump(users, f, indent=4)

    return redirect(url_for('auth_bp.settings'))