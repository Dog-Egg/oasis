import zangar as z
from flask import Flask
from flask_oasis import MediaType, PathTemplate, Resource, input, output, responseify


class MyAPI(Resource):
    @input.cookie("language", required=False, schema=z.str())
    @output.response(200, content={"application/json": MediaType()})
    def get(self, language=None):
        if language == "zh":
            return responseify({"message": "你好，世界!"})
        return responseify({"message": "Hello World!"})


paths = {
    PathTemplate("/myapi"): MyAPI,
}

app = Flask(__name__)
for path, resource in paths.items():
    app.add_url_rule(path.flask_path, view_func=resource.as_view())
