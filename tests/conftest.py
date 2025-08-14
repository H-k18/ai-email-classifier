import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os
import sys

# This line is no longer needed if you have pytest.ini
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    db_path = "test_app.db"
    db_uri = 'sqlite:///' + os.path.join(os.path.dirname(__file__), db_path)
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    full_db_path = os.path.join(os.path.dirname(__file__), db_path)
    if os.path.exists(full_db_path):
        os.unlink(full_db_path)

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

# --- NEW FIXTURE ---
@pytest.fixture()
def logged_in_client(client, app):
    """A test client that is already logged in."""
    # 1. Create a user directly in the test database
    with app.app_context():
        test_user = User(
            username='test@example.com',
            password=generate_password_hash('password123', method='pbkdf2:sha256')
        )
        db.session.add(test_user)
        db.session.commit()

    # 2. Log the user in
    client.post('/login', data={
        'username': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)

    yield client # The test will run with this client

    # 3. Clean up by logging out
    client.get('/logout', follow_redirects=True)