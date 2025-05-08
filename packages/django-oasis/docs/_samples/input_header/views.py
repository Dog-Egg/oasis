import zangar as z
from django_oasis import MediaType, Resource, input, output, responseify


class MyAPI(Resource):
    @input.header("language", z.str(), required=False)
    @output.response(200, content={"application/json": MediaType()})
    def get(self, request, language=None):
        if language == "zh":
            return responseify({"message": "你好，世界!"})
        else:
            return responseify({"message": "Hello World!"})
