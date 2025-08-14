def test_main_page_redirects_when_not_logged_in(client):
    """
    Tests that accessing the main page without being logged in
    redirects to the login page.
    """
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login to AI Classifier" in response.data

def test_api_is_protected(client):
    """
    Tests that API endpoints are protected and require login.
    """
    response_emails = client.get('/get_emails')
    assert response_emails.status_code == 302 # 302 is a redirect

    response_categories = client.get('/get_categories')
    assert response_categories.status_code == 302