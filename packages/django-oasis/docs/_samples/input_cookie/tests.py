from django.test import RequestFactory

from .views import MyAPI


def test_requests():
    rf = RequestFactory()
    request = rf.get("")

    request.COOKIES = {"language": "en"}
    view = MyAPI.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.content == b'{"message": "Hello World!"}'

    request.COOKIES = {"language": "zh"}
    response = view(request)
    assert response.status_code == 200
    assert response.content == '{"message": "你好，世界!"}'.encode("unicode-escape")
