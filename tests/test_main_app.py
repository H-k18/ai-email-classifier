from app.models import Email, Category, db

def test_online_learning_and_persistence(logged_in_client, app):
    """
    Tests that the learning mechanism correctly saves changes to the database,
    which is the most reliable way to verify the feature.
    """
    learning_email_body = "we have a new job opening for a python developer"
    
    # --- 1. Initial State ---
    # Create an email in the database that is initially 'primary'.
    with app.app_context():
        user_id = 1
        primary_cat = Category.query.filter_by(name='primary', user_id=user_id).first()
        if not primary_cat:
            primary_cat = Category(name='primary', user_id=user_id)
            db.session.add(primary_cat)
        
        test_email = Email(
            sender='test sender', 
            subject='test subject', 
            body=learning_email_body, 
            user_id=user_id,
            category=primary_cat
        )
        db.session.add(test_email)
        db.session.commit()
        email_id_to_correct = test_email.id

    # --- 2. User Correction ---
    # Send a request to learn the new, more specific category.
    learn_response = logged_in_client.post('/learn', json={
        'email_id': email_id_to_correct,
        'email_text': learning_email_body,
        'correct_label': 'job postings'
    })
    assert learn_response.status_code == 200

    # --- 3. Verify Database Changes (The Definitive Test) ---
    with app.app_context():
        # Check 1: Was the email's category changed in the database?
        corrected_email = Email.query.get(email_id_to_correct)
        assert corrected_email is not None
        assert corrected_email.category.name == 'job postings'

        # Check 2: Was the new category created in the database for this user?
        new_category = Category.query.filter_by(name='job postings', user_id=user_id).first()
        assert new_category is not None