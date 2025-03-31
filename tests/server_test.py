import pytest
from app import app  # Import the Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client  # Provide the test client to the test functions

def test_home_route(client):
    response = client.get("/")  # Make a GET request to "/"
    assert response.status_code == 200  # Check if the response is 200 OK

    response2 = client.get("/execute")  # Make a GET request to "/execute"
    assert response2.status_code == 405  # Check if the response is 405 Method Not Allowed
