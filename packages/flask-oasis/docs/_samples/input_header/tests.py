from .app import app


def test_requests():
    with app.test_client() as client:
        response = client.get("/myapi", headers={"LANGUAGE": "zh"})
        assert response.request.headers["LANGUAGE"] == "zh"
        assert response.status_code == 200
        assert response.json == {"message": "你好，世界!"}

        response = client.get("/myapi", headers={"LANGUAGE": "en"})
        assert response.status_code == 200
        assert response.json == {"message": "Hello World!"}
