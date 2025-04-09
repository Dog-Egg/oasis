import pytest
import zangar as z
from flask import Flask
from flask_oasis import MediaType, Resource, Router, input

router = Router()
router.add_url("/", Resource)


@pytest.fixture
def app():
    app = Flask(__name__)
    router.register_with(app)
    yield app


@pytest.fixture
def client(app):
    yield app.test_client()


def test_http_405(client):
    response = client.post("/")
    assert response.status_code == 405


def test_http_415(app):
    class MyResource(Resource):
        @input.body(
            "body", content={"application/json": MediaType(z.struct({"a": z.int()}))}
        )
        def post(self, body): ...

    with app.test_request_context(
        "/",
        method="POST",
        content_type="text/xxx",
    ):
        response = MyResource.as_view()()
        assert response.status_code == 415


def test_http_422(app):
    class MyResource(Resource):
        @input.query("a", z.int())
        def get(self, request, a): ...

        @input.body(
            "body", content={"application/json": MediaType(z.struct({"a": z.int()}))}
        )
        def post(self, request, body): ...

    view = MyResource.as_view()
    with app.test_request_context(
        "/",
        method="POST",
        data='{"a": "abc"}',
        content_type="application/json",
    ):
        response = view()
        assert response.status_code == 422
        assert response.json == {
            "in": "body",
            "errors": [{"loc": ["a"], "msgs": ["Expected int, received str"]}],
        }

    with app.test_request_context(
        "/?a=abc",
        method="GET",
    ):
        response = view()
        assert response.status_code == 422
        assert (response.json) == {
            "in": "query",
            "errors": [{"loc": ["a"], "msgs": ["Expected int, received str"]}],
        }
