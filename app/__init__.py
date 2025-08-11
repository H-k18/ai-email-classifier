# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .user_model import User
import json
import os

# --- DATABASE FILE PATHS ---
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
USERS_DB_PATH = os.path.join(BASE_DIR, 'users.json')

# Initialize extensions
mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'

    # --- CONFIGURE FLASK-MAIL ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    # Initialize extensions with the app
    mail.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth_bp.login'

    @login_manager.user_loader
    def load_user(user_id):
        # --- THIS IS THE FIX --- Make user loading robust
        if not os.path.exists(USERS_DB_PATH):
            return None
        try:
            with open(USERS_DB_PATH, 'r') as f:
                users = json.load(f)
        except json.JSONDecodeError:
            return None # Return None if the file is empty or corrupted

        for user_data in users:
            if user_data['id'] == int(user_id):
                return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password'])
        return None

    # Import and register blueprints
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app