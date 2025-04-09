import zangar as z
from flask_oasis import MediaType, Resource, input, output, responseify


class MyAPI(Resource):
    @input.cookie("language", required=False, schema=z.str())
    @output.response(200, content={"application/json": MediaType()})
    def get(self, language=None):
        if language == "zh":
            return responseify({"message": "你好，世界!"})
        return responseify({"message": "Hello World!"})
