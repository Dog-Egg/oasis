from django.test import RequestFactory

from .views import Greeting


def test_request():
    rf = RequestFactory()
    request = rf.get("/?name=tom")

    response = Greeting.as_view()(request)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.content == b'{"message": "Hello Tom"}'
