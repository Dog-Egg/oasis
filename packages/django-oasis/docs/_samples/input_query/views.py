import zangar as z
from django_oasis import MediaType, Resource, input, output, responseify


class MyAPI(Resource):
    @input.query("name", schema=z.str())
    @output.response(200, content={"text/plain": MediaType()})
    def get(self, request, name):
        return responseify(f"Hello, {name}!")
