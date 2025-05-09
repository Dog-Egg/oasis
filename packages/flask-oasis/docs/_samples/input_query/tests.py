from .app import app


def test_requests():
    with app.test_client() as client:
        response = client.get("/myapi?name=John")
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.data.decode() == "Hello, John!"
