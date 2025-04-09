from flask import Flask

from .urls import router


def test_requests():
    app = Flask(__name__)
    router.register_with(app)
    with app.test_client() as client:
        response = client.get("/users/1")
        assert response.status_code == 200
        assert response.json == {"id": 1, "name": "James", "age": 20}

        response = client.get("/users/1000")
        assert response.status_code == 404
