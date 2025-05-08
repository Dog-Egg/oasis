from .app import app


def test_requests():
    with app.test_client() as client:
        response = client.get("/users/1")
        assert response.status_code == 200
        assert response.json == {"id": 1, "name": "James", "age": 20}

        response = client.get("/users/1000")
        assert response.status_code == 404
