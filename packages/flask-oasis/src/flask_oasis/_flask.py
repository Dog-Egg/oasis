from __future__ import annotations

from flask import current_app, jsonify, make_response, request
from oasis_shared import (
    HTTP_METHODS,
    CookieBase,
    HeaderBase,
    ParameterDecoratorBase,
    PathBase,
    PathTemplateBase,
    QueryBase,
    RequestBodyDecoratorBase,
    ResourceBase,
    catch_throw,
    resource_ctx,
)
from werkzeug.datastructures import Headers
from zangar.exceptions import ValidationError


class Query(QueryBase):
    def get_argumentset(self, *args, **kwargs):
        return request.args


class _HeadersMapping(dict):
    def __init__(self, header: Headers):
        self.headers = header

    def __getitem__(self, key):
        return self.headers.get(key)


class Header(HeaderBase):
    def get_argumentset(self, *args, **kwargs):
        return _HeadersMapping(request.headers)


class Cookie(CookieBase):
    def get_argumentset(self, *args, **kwargs):
        return request.cookies


class Path(PathBase):
    def get_argumentset(self, *args, **kwargs):
        return request.view_args

    def modify_args(self, *args, **kwargs):
        del kwargs[self.name]
        return args, kwargs


class ParameterDecorator(ParameterDecoratorBase):
    def process_schema_parsing_exception(self, e: ValidationError):
        return _process_schema_parsing_exception(e, self.param.location)


def query(*args, **kwargs):
    return ParameterDecorator(Query(*args, **kwargs))


def path(*args, **kwargs):
    return ParameterDecorator(Path(*args, **kwargs))


def cookie(*args, **kwargs):
    return ParameterDecorator(Cookie(*args, **kwargs))


def header(*args, **kwargs):
    return ParameterDecorator(Header(*args, **kwargs))


def _json_response_processor(kwargs):
    return make_response(jsonify(kwargs["data"]), kwargs["status"])


def _json_request_processor():
    return request.json


def _form_request_processor():
    return request.form


def _text_response_processor(kwargs):
    response = make_response(kwargs["data"], kwargs["status"])
    response.mimetype = "text/plain"
    return response


class Resource(ResourceBase):
    request_content_processors = {
        "application/json": _json_request_processor,
        "application/x-www-form-urlencoded": _form_request_processor,
    }
    response_content_processors = {
        "application/json": _json_response_processor,
        "text/plain": _text_response_processor,
    }

    def dispatch(self, *args, **kwargs):
        return getattr(self, request.method.lower())(*args, **kwargs)

    @classmethod
    def as_view(cls):
        @catch_throw
        def view(*args, **kwargs):
            with resource_ctx(cls):
                return cls().dispatch(*args, **kwargs)

        view.methods = [
            method.upper() for method in HTTP_METHODS if hasattr(cls, method)
        ]
        view.__name__ = cls.__name__

        return view


class RequestBodyDecorator(RequestBodyDecoratorBase):
    def request_media_type(self, *args, **kwargs):
        return request.content_type

    def is_response(self, response):
        return isinstance(response, current_app.response_class)

    def unsupported_media_type(self):
        return current_app.response_class(status=415)

    def process_schema_parsing_exception(self, e: ValidationError):
        return _process_schema_parsing_exception(e, "body")


def _process_schema_parsing_exception(e: ValidationError, location: str):
    return make_response(jsonify({"in": location, "errors": e.format_errors()}), 422)


def body(*args, **kwargs):
    return RequestBodyDecorator(*args, **kwargs)


class PathTemplate(PathTemplateBase):
    @property
    def flask_path(self):
        parts = []
        for part in self._parts:
            if isinstance(part, str):
                parts.append(part)
            else:
                parts.append(
                    f"<{part.variable}>"
                    if part.converter is None
                    else f"<{part.converter}:{part.variable}>"
                )
        return "/" + "/".join(parts)
