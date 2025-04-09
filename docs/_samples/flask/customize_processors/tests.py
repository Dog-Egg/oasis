import yaml
from flask import Flask

from .processors import yaml_request_processor, yaml_response_processor
from .urls import router


def test_request():
    app = Flask(__name__)
    app.config.update(
        {
            "OASIS_REQUEST_CONTENT_PROCESSORS": {
                "application/yaml": yaml_request_processor.__module__
                + "."
                + yaml_request_processor.__name__,
            },
            "OASIS_RESPONSE_CONTENT_PROCESSORS": {
                "application/yaml": "%s:%s"
                % (yaml_response_processor.__module__, yaml_response_processor.__name__)
            },
        }
    )
    router.register_with(app)
    with app.test_client() as client:
        response = client.post(
            "/myapi",
            data=yaml.safe_dump({"name": "Tom", "age": 18}),
            content_type="application/yaml",
        )

        assert response.request.mimetype == "application/yaml"
        assert response.status_code == 200
        assert response.data == b"name: Tom\nage: 18\n"
        assert response.mimetype == "application/yaml"
