from app.models import Email, Category, db

def test_online_learning_and_generalization(logged_in_client, app):
    """
    Tests the full online learning cycle and the model's ability to generalize
    using a realistic, ambiguous email.
    """
    # Use an email that the model will initially classify as 'primary'.
    learning_email_body = "we have a new job opening for a python developer"
    
    # --- 1. Initial Prediction ---
    # The model should correctly identify this as a legitimate, primary email.
    response = logged_in_client.post('/predict', json={'email_text': learning_email_body})
    assert response.status_code == 200
    assert response.json['prediction'] == 'primary'

    # --- 2. User Correction ---
    # Now, we teach the model a more specific category: "job postings".
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

    # We teach it multiple times to build the AI's confidence in the new category.
    for _ in range(10): 
        learn_response = logged_in_client.post('/learn', json={
            'email_id': email_id_to_correct,
            'email_text': learning_email_body,
            'correct_label': 'job postings'
        })
        assert learn_response.status_code == 200

    # --- 3. Verify In-Memory Learning ---
    # The AI should now predict the new, more specific category for the same text.
    response_after_learning = logged_in_client.post('/predict', json={'email_text': learning_email_body})
    assert response_after_learning.status_code == 200
    assert response_after_learning.json['prediction'] == 'job postings'

    # --- 4. Verify Generalization ---
    # Test with a different but similar email.
    generalization_email_body = "microsoft has a project manager opening"
    response_generalization = logged_in_client.post('/predict', json={'email_text': generalization_email_body})
    assert response_generalization.status_code == 200
    # The model should now generalize and classify this new email as 'job postings'.
    assert response_generalization.json['prediction'] == 'job postings'