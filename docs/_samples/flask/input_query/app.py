import zangar as z
from flask import Flask
from flask_oasis import MediaType, PathTemplate, Resource, input, output, responseify


class MyAPI(Resource):
    @input.query("name", schema=z.str())
    @output.response(200, content={"text/plain": MediaType()})
    def get(self, name):
        return responseify(f"Hello, {name}!")


paths = {
    PathTemplate("/myapi"): MyAPI,
}

app = Flask(__name__)
for path, resource in paths.items():
    app.add_url_rule(path.flask_path, view_func=resource.as_view())
