from __future__ import annotations

import zangar as z
from flask import Flask
from flask_oasis import MediaType, PathTemplate, Resource, input, output, responseify


class MyAPI(Resource):
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
