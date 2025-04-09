from flask import Flask

from .urls import router


def test_requests():
    app = Flask(__name__)
    router.register_with(app)
    with app.test_client() as client:
        client.set_cookie("LANGUAGE", "en")
        response = client.get("/myapi")

        assert response.status_code == 200
        assert response.json == {"message": "Hello World!"}

        client.set_cookie("language", "zh")
        response = client.get("/myapi")
        assert response.status_code == 200
        assert response.json == {"message": "你好，世界!"}
