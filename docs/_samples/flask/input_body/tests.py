from urllib.parse import urlencode

from flask import Flask

from .urls import router


def test_requests():
    app = Flask(__name__)
    router.register_with(app)
    with app.test_client() as client:
        response = client.post(
            "/login",
            data=urlencode({"username": "admin", "password": "test"}),
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "Welcome, admin!"
