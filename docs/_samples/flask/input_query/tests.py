from flask import Flask

from .urls import router


def test_requests():
    app = Flask(__name__)
    router.register_with(app)
    with app.test_client() as client:
        response = client.get("/myapi?name=John")
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.data.decode() == "Hello, John!"
