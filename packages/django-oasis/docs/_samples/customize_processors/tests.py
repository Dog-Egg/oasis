import yaml
from django.test import RequestFactory

from .views import MyAPI


def test_requests():
    rf = RequestFactory()
    request = rf.generic(
        "POST",
        "/",
        data=yaml.safe_dump({"name": "Tom", "age": 18}),
        content_type="application/yaml",
    )

    view = MyAPI.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.content == b"name: Tom\nage: 18\n"
