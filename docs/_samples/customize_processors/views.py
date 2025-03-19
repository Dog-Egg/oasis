import zangar as z
from django_oasis import MediaType, Resource, input, output, responseify


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
    def post(self, request, body):
        return responseify(body)
