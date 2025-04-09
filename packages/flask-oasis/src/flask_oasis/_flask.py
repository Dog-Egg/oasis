from __future__ import annotations

from flask import Blueprint, Flask, current_app, jsonify, make_response, request
from oasis_shared import (
    HTTP_METHODS,
    CookieBase,
    HeaderBase,
    ParameterDecoratorBase,
    PathBase,
    QueryBase,
    RequestBodyDecoratorBase,
    ResourceBase,
    RouterBase,
    responseify_base,
)
from werkzeug.datastructures import Headers
from werkzeug.utils import import_string
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


class Resource(ResourceBase):
    def dispatch(self, *args, **kwargs):
        return getattr(self, request.method.lower())(*args, **kwargs)

    @classmethod
    def as_view(cls):
        def view(*args, **kwargs):
            return cls().dispatch(*args, **kwargs)

        view.methods = [
            method.upper() for method in HTTP_METHODS if hasattr(cls, method)
        ]
        view.__name__ = cls.__name__

        return view


class Router(RouterBase):
    def register_with(self, scaffold: Blueprint | Flask, /):
        for item in self._items:
            view = item.resource.as_view()

            parts = []
            for part in item.split_path:
                if isinstance(part, str):
                    parts.append(part)
                else:
                    parts.append(
                        f"<{part.variable}>"
                        if part.converter is None
                        else f"<{part.converter}:{part.variable}>"
                    )
            scaffold.add_url_rule("/" + "/".join(parts), view_func=view)


def responseify(*args, **kwargs):
    from . import processors

    default_processors = {
        "application/json": processors.json_response_processor,
        "text/plain": processors.text_response_processor,
    }

    def get_processor(media_type):
        processors = current_app.config.get("OASIS_RESPONSE_CONTENT_PROCESSORS", {})
        if media_type in processors:
            return import_string(processors[media_type])
        return default_processors[media_type]

    return responseify_base(*args, **kwargs, get_processor=get_processor)


class RequestBodyDecorator(RequestBodyDecoratorBase):
    def request_media_type(self, *args, **kwargs):
        return request.content_type

    def get_processor(self, media_type):
        from . import processors

        default_processors = {
            "application/json": processors.json_request_processor,
            "application/x-www-form-urlencoded": processors.form_request_processor,
        }

        processors = current_app.config.get("OASIS_REQUEST_CONTENT_PROCESSORS", {})
        if media_type in processors:
            return import_string(processors[media_type])
        return default_processors[media_type]

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
