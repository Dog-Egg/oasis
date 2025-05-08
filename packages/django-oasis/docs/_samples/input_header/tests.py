from django.test import RequestFactory

from .views import MyAPI


def test_requests():
    rf = RequestFactory()
    view = MyAPI.as_view()

    request = rf.get("", headers={"LANGUAGE": "zh"})
    response = view(request)
    assert response.status_code == 200
    assert response.content == '{"message": "你好，世界!"}'.encode("unicode-escape")

    request = rf.get("", headers={"LANGUAGE": "en"})
    response = view(request)
    assert response.status_code == 200
    assert response.content == b'{"message": "Hello World!"}'
