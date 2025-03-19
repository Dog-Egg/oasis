import zangar as z
from django_oasis import MediaType, Resource, input, output


class MyAPI(Resource):
    @input.query("name", schema=z.str())
    @output.response(200, content={"text/plain": MediaType()})
    def get(self, name):
        return f"Hello, {name}!"
