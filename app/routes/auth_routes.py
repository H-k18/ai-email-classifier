# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from app import mail  # Import the mail instance
from app.user_model import User
import json
import os
import random

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