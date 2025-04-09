import zangar as z
from flask_oasis import MediaType, Resource, input, output, responseify


class MyAPI(Resource):
    @input.query("name", schema=z.str())
    @output.response(200, content={"text/plain": MediaType()})
    def get(self, name):
        return responseify(f"Hello, {name}!")
