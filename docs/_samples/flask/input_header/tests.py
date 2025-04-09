from flask import Flask

from .urls import router


def test_requests():
    app = Flask(__name__)
    router.register_with(app)
    with app.test_client() as client:
        response = client.get("/myapi", headers={"LANGUAGE": "zh"})
        assert response.request.headers["LANGUAGE"] == "zh"
        assert response.status_code == 200
        assert response.json == {"message": "你好，世界!"}

        response = client.get("/myapi", headers={"LANGUAGE": "en"})
        assert response.status_code == 200
        assert response.json == {"message": "Hello World!"}
