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
