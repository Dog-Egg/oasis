import yaml
from django.test import RequestFactory, override_settings

from .processors import yaml_request_processor, yaml_response_processor
from .views import MyAPI


@override_settings(
    OASIS_REQUEST_CONTENT_PROCESSORS={
        "application/yaml": yaml_request_processor.__module__
        + "."
        + yaml_request_processor.__name__,
    },
    OASIS_RESPONSE_CONTENT_PROCESSORS={
        "application/yaml": yaml_response_processor.__module__
        + "."
        + yaml_response_processor.__name__,
    },
)
def test_request():
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
