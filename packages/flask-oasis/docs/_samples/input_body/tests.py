from urllib.parse import urlencode

from .app import app


def test_requests():
    with app.test_client() as client:
        response = client.post(
            "/login",
            data=urlencode({"username": "admin", "password": "test"}),
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "Welcome, admin!"
