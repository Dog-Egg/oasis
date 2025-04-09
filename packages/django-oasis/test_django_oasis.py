import json

import pytest
import zangar as z
from bs4 import BeautifulSoup
from django.test import RequestFactory
from django_oasis import MediaType, Resource, Router, input, output, responseify
from django_oasis.settings import user_settings


def test_http_405():
    view = Resource.as_view()
    response = view(RequestFactory().get(""))
    assert response.status_code == 405


def test_http_422():
    class MyResource(Resource):
        @input.query("a", z.int())
        def get(self, request, a): ...

        @input.body(
            "body", content={"application/json": MediaType(z.struct({"a": z.int()}))}
        )
        def post(self, request, body): ...

    view = MyResource.as_view()
    response = view(RequestFactory().get("/?a=abc"))
    assert response.status_code == 422
    assert json.loads(response.content) == {
        "in": "query",
        "errors": [{"loc": ["a"], "msgs": ["Expected int, received str"]}],
    }

    response = view(
        RequestFactory().post(
            "/", data=json.dumps({"a": "abc"}), content_type="application/json"
        )
    )
    assert response.status_code == 422
    assert json.loads(response.content) == {
        "in": "body",
        "errors": [
            {
                "loc": ["a"],
                "msgs": ["Expected int, received str"],
            }
        ],
    }


def test_http_400():
    class MyResource(Resource):
        @input.body(
            "body", content={"application/json": MediaType(z.struct({"a": z.int()}))}
        )
        def post(self, request, body): ...

    view = MyResource.as_view()
    response = view(
        RequestFactory().post("/", data="abc", content_type="application/json")
    )
    assert response.status_code == 400
    assert (response.content) == b"Invalid JSON"


def test_http_415():
    class MyResource(Resource):
        @input.body(
            "body", content={"application/json": MediaType(z.struct({"a": z.int()}))}
        )
        def post(self, request, body): ...

    view = MyResource.as_view()
    response = view(RequestFactory().post("/", data="abc", content_type="text/plain"))
    assert response.status_code == 415


def test_router_add_url():
    router = Router()
    with pytest.raises(ValueError) as e:
        router.add_url("api", Resource)
    assert e.value.args == ("path must start with '/'",)


def test_responseify():
    @output.response(200, content={"text/plain": MediaType(z.str())})
    @output.response(201, content={"text/plain": MediaType(z.str())})
    def view():
        return responseify("Hello, world!")

    with pytest.raises(RuntimeError) as e:
        view()
    assert e.value.args == ("Multiple MediaType found",)

    @output.response(200, content={"text/plain": MediaType(z.str())})
    def view2():
        return responseify("Hello, world!", media_type="text/html")

    with pytest.raises(RuntimeError) as e:
        view2()
    assert e.value.args == ("No MediaType found",)


def test_user_settings():
    with pytest.raises(AttributeError):
        user_settings.UNKNOWN


def test_swagger_ui():
    from django_oasis.docs import swagger_ui

    view = swagger_ui({"url": "https://example.com/swagger.json"})

    response = view(RequestFactory().get("/"))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    tag = soup.find("script", id="config-data")
    assert tag is not None
    assert tag.text == '{"url": "https://example.com/swagger.json"}'
    etag = response["ETag"]

    response = view(RequestFactory().get("/", headers={"if-none-match": etag}))
    assert response.status_code == 304


@output.response(200, content={"text/plain": MediaType()})
def test_responseif_content_type():
    with pytest.warns(DeprecationWarning):
        responseify(
            "Hello, World!",
            content_type="text/plain",
        )
