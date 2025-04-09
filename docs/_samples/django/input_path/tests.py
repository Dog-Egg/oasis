from django.test import Client, override_settings

from . import urls


@override_settings(ROOT_URLCONF=urls)
def test_requests():
    client = Client()
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "James", "age": 20}

    response = client.get("/users/1000")
    assert response.status_code == 404
