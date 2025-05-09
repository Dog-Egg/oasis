import yaml
from flask import make_response, request


def yaml_request_processor():
    try:
        return yaml.safe_load(request.data)
    except yaml.YAMLError:
        return make_response("Invalid YAML", 400, {"Content-Type": "text/plain"})


def yaml_response_processor(kwargs):
    return make_response(
        yaml.safe_dump(kwargs["data"], sort_keys=False),
        kwargs["status"],
        {"Content-Type": "application/yaml"},
    )
