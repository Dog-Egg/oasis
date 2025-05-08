from __future__ import annotations

import yaml
import zangar as z
from flask import Flask, make_response, request
from flask_oasis import MediaType, PathTemplate, Resource, input, output, responseify


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
    def post(self, body):
        return responseify(body)


paths: dict[PathTemplate, type[Resource]] = {
    PathTemplate("/myapi"): MyAPI,
}

app = Flask(__name__)
for path, resource in paths.items():
    app.add_url_rule(path.flask_path, view_func=resource.as_view())
