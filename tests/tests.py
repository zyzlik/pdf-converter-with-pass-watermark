from app import app

def test_ping():
    # Create a test client using the Flask application configured for testing
    response = app.test_client().get('/')
    assert response.status_code != 200

test_ping()