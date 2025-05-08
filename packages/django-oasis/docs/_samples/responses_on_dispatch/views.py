import zangar as z
from django_oasis import MediaType, Resource, input, output, responseify


class Greeting(Resource):
    @output.response(
        422,
        content={"application/json": MediaType(z.struct({"errors": z.list(z.str())}))},
    )
    def dispatch(self, request):
        return super().dispatch(request)

    @input.query("name", schema=z.str().transform(lambda s: s.title()))
    @output.response(
        200, content={"application/json": MediaType(z.struct({"message": z.str()}))}
    )
    def get(self, request, name):
        return responseify({"message": f"Hello {name}"}, status=200)
