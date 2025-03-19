from urllib.parse import urlencode

from django.test import RequestFactory

from . import views


def test_requests():
    rf = RequestFactory()
    request = rf.post(
        "/",
        data=urlencode({"username": "admin", "password": "test"}),
        content_type="application/x-www-form-urlencoded",
    )
    view = views.Login.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.content == b"Welcome, admin!"
