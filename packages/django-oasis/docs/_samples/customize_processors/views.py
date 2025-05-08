import yaml
import zangar as z
from django.http import HttpRequest, HttpResponse
from django_oasis import MediaType, Resource, input, output, responseify


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


class MyAPI(Resource):
    request_content_processors = {
        "application/yaml": yaml_request_processor,
    }
    response_content_processors = {
        "application/yaml": yaml_response_processor,
    }

    @input.body(
        "body",
        content={
            "application/yaml": MediaType(
                z.struct(
                    {
                        "name": z.str(),
                        "age": z.int(),
                    }
                )
            ),
        },
    )
    @output.response(
        200,
        content={
            "application/yaml": MediaType(
                z.struct(
                    {
                        "name": z.str(),
                        "age": z.int(),
                    }
                )
            ),
        },
    )
    def post(self, request, body):
        return responseify(body)
