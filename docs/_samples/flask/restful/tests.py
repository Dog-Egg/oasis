import pytest
from flask import Flask
from flask.testing import FlaskClient

from .urls import router


@pytest.fixture
def client():
    app = Flask(__name__)
    router.register_with(app)
    yield app.test_client()


def test_users_get(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json == {
        "users": [
            {"id": 1, "name": "James"},
            {"id": 2, "name": "Linda"},
            {"id": 3, "name": "Emily"},
        ],
        "page": 1,
        "page_size": 10,
    }


def test_users_get_page(client):
    response = client.get("/users?page=2&page_size=1")
    assert response.json == {
        "users": [{"id": 2, "name": "Linda"}],
        "page": 2,
        "page_size": 1,
    }


def test_users_post(client: FlaskClient):
    response = client.post("/users", json={"name": "Tom"})
    assert response.status_code == 201
    assert response.json == {"id": 4, "name": "Tom"}


def test_user_get(client):
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json == {"id": 1, "name": "James"}


def test_user_patch(client):
    response = client.patch("/users/1", json={"name": "Tom"})
    assert response.status_code == 200
    assert response.json == {"id": 1, "name": "Tom"}


def test_user_delete(client):
    response = client.delete("/users/1")
    assert response.status_code == 204
