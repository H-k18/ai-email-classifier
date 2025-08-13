# app/models.py
from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """Database model for user accounts."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False) # User's email
    password = db.Column(db.String(150), nullable=False) # Hashed password for our app
    
    # Encrypted credentials for email polling
    imap_server = db.Column(db.String(150), default='imap.gmail.com')
    encrypted_email = db.Column(db.String(500))
    encrypted_password = db.Column(db.String(500)) # Encrypted 16-digit App Password

    # Relationships
    emails = db.relationship('Email', backref='owner', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', backref='owner', lazy=True, cascade="all, delete-orphan")

class Email(db.Model):
    """Database model for individual emails."""
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys to link to other tables
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Category(db.Model):
    """Database model for user-defined categories/folders."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Foreign Key to link to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship
    emails = db.relationship('Email', backref='category', lazy=True)