import zangar as z
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette_oasis import Resource, input


def test_http_405():
    class MyResource(Resource):
        async def post(self, request):
            return Response()  # pragma: no cover

    client = TestClient(Route("/", MyResource))
    response = client.get("/")
    assert response.status_code == 405


def test_http_415():
    class MyResource(Resource):
        @input.body("body", content={"application/json": {}})
        async def post(self, request):
            return Response()  # pragma: no cover

    client = TestClient(Route("/", MyResource))
    response = client.post("/", headers={"content-type": "text/plain"})
    assert response.status_code == 415


def test_http_422():
    class MyResource(Resource):
        @input.query("query", z.to.int())
        @input.body("body", content={"application/json": z.int()})
        async def post(self, request): ...

    client = TestClient(Route("/", MyResource))
    response = client.post("/?query=a")
    assert response.status_code == 422
    assert response.json() == {
        "errors": [
            {
                "loc": ["query"],
                "msgs": ["Cannot convert the value 'a' to int"],
            }
        ],
        "in": "query",
    }

    response = client.post("/?query=1", json="a")
    assert response.status_code == 422
    assert response.json() == {
        "in": "body",
        "errors": [
            {
                "msgs": ["Expected int, received str"],
            }
        ],
    }
