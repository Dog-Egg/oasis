import yaml
from django.http import HttpRequest, HttpResponse


def yaml_request_processor(request: HttpRequest):
    try:
        return yaml.safe_load(request.body)
    except yaml.YAMLError:
        return HttpResponse("Invalid YAML", status=400, content_type="text/plain")


def yaml_response_processor(kwargs):
    return HttpResponse(
        yaml.safe_dump(kwargs["data"], sort_keys=False),
        status=kwargs["status"],
        content_type="application/yaml",
    )
