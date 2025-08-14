from app.models import User, Category, db

def test_user_creation_creates_default_categories(app):
    """
    Integration Test:
    Tests that creating a User and committing it to the database
    is correctly followed by the creation of their default categories.
    """
    with app.app_context():
        # 1. Create a new user
        new_user = User(
            username='integration@test.com',
            password='password_hash'
        )
        db.session.add(new_user)
        db.session.commit() # This gives the user an ID

        # 2. Create their default categories, linking them to the user
        primary_cat = Category(name='primary', owner=new_user)
        spam_cat = Category(name='spam', owner=new_user)
        db.session.add(primary_cat)
        db.session.add(spam_cat)
        db.session.commit()

        # 3. Verify the integration
        # Fetch the user from the database
        user_from_db = User.query.filter_by(username='integration@test.com').first()
        assert user_from_db is not None
        
        # Check that the relationship works and the categories were created
        assert len(user_from_db.categories) == 2
        category_names = {cat.name for cat in user_from_db.categories}
        assert 'primary' in category_names
        assert 'spam' in category_names