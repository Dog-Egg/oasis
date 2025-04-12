import os
import types

import yaml
from django.test import RequestFactory, override_settings

from .views import MyAPI

settings_module = types.ModuleType("settings")
with open(os.path.join(os.path.dirname(__file__), "settings.py")) as f:
    code = f.read()
    code = code.replace(
        "<your-processors-module>", "_samples.django.customize_processors.processors"
    )
exec(code, settings_module.__dict__)


@override_settings(**{k: v for k, v in vars(settings_module).items() if k.isupper()})
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
