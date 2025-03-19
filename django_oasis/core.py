from __future__ import annotations

import functools
import itertools
import re
from collections import ChainMap
from collections.abc import Callable, Hashable
from contextvars import ContextVar
from http import HTTPStatus
from typing import Any, NamedTuple, cast

import zangar as z
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBase
from django.utils.module_loading import import_string

from django_oasis import settings

_METHODS = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]


class Resource:
    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        if method in _METHODS and hasattr(self, method):
            return getattr(self, method)(request, *args, **kwargs)
        return HttpResponse(status=405)

    @classmethod
    def as_view(cls):
        def view(*args, **kwargs):
            # 每个请求都会创建一个新的 Resoruce 实例，这意味即使将数据写入 self 也是安全的。
            return cls().dispatch(*args, **kwargs)

        return view

    @classmethod
    def spec(cls, openapi: str):
        """Path Item Object of OAS"""

        rv = {}

        definitions = getattr(cls.dispatch, _OAS_DEFINITIONS, [])
        method_defintions = []
        for definition in reversed(definitions):
            if isinstance(definition, RequestParameterObject):
                set_dict(
                    rv, ["parameters"], lambda x: (x or []) + [definition.spec(openapi)]
                )
            else:
                method_defintions.append(definition)

        for method in _METHODS:
            if not hasattr(cls, method):
                continue

            func = getattr(cls, method)
            definitions = getattr(func, _OAS_DEFINITIONS, [])
            for definition in itertools.chain(method_defintions, reversed(definitions)):
                if isinstance(definition, RequestParameterObject):
                    set_dict(
                        rv,
                        [method, "parameters"],
                        lambda x: (x or []) + [definition.spec(openapi)],
                    )
                elif isinstance(definition, ResponseObject):
                    set_dict(
                        rv,
                        [method, "responses", str(definition.status)],
                        lambda _: definition.spec(openapi),
                    )
                elif isinstance(definition, RequestBodyObject):
                    set_dict(
                        rv,
                        [method, "requestBody"],
                        lambda _: definition.spec(openapi),
                    )
                else:
                    raise NotImplementedError(f"Unknown definition: {definition}")
        return rv


def _get_schema_spec(schema, openapi: str):
    if tuple(map(int, openapi.split(".")))[:2] == (3, 0):
        from zangar.compilation import OpenAPI30Compiler

        return OpenAPI30Compiler().compile(schema)
    raise NotImplementedError(f"Unsupported openapi: {openapi}")


class MediaType:
    def __init__(self, schema: z.Schema | None = None):
        self.__schema = schema

    def spec(self, openapi: str):
        rv = {}
        if self.__schema:
            rv["schema"] = _get_schema_spec(self.__schema, openapi)
        return rv

    def parse(self, value):
        if self.__schema:
            return self.__schema.parse(value)
        return value


class ResponseObject:
    def __init__(
        self,
        status: int,
        content: dict[str, MediaType] | None = None,
        description=None,
    ) -> None:
        self.status = status
        self.__content = content
        self.description = description

    def spec(self, openapi: str):
        rv = {
            "description": self.description or HTTPStatus(self.status).phrase,
        }
        if self.__content:
            rv["content"] = {
                content_type: content.spec(openapi)
                for content_type, content in self.__content.items()
            }
        return rv


class RequestParameterObject:
    location: str

    def __init__(
        self,
        name,
        /,
        schema: z.Schema,
        *,
        required=True,
        description: str | None = None,
    ):
        self.name = name
        self.__schema = schema
        self.__required = required
        self.__description = description

    def spec(self, openapi: str):
        rv = {
            "name": self.name,
            "in": self.location,
        }
        if self.__schema:
            rv["schema"] = _get_schema_spec(self.__schema, openapi)
        if self.__required:
            rv["required"] = True
        if self.__description is not None:
            rv["description"] = self.__description
        return rv

    def parse_request(self, request):
        if isinstance(self.__schema, (z.struct, z.dataclass)):
            argumentset = {self.name: self.get_argumentset(request)}
        else:
            argumentset = self.get_argumentset(request)

        field = z.field(self.__schema)
        if not self.__required:
            field = field.optional()
        return z.struct({self.name: field}).parse(argumentset)

    def get_argumentset(self, request):
        raise NotImplementedError(self)

    def modify_args(self, *args, **kwargs):
        return args, kwargs


_OAS_DEFINITIONS = "__oasis_definitions"


def set_oas_definition(func, definition):
    if not hasattr(func, _OAS_DEFINITIONS):
        setattr(func, _OAS_DEFINITIONS, [])
    getattr(func, _OAS_DEFINITIONS).append(definition)


def set_dict(data: dict, path: list[Hashable], setter: Callable[[Any], Any]):
    """
    >>> data = {}
    >>> set_dict(data, ["a", "b"], lambda x: (x or []) + [1])
    {'a': {'b': [1]}}
    >>> set_dict(data, ["a", "b"], lambda x: (x or []) + [2])
    {'a': {'b': [1, 2]}}
    """
    d = data
    for index, key in enumerate(path):
        if index == len(path) - 1:
            d[key] = setter(d.get(key))
        else:
            d = d.setdefault(key, {})
    return data


class Router:
    def __init__(self):
        self.__django_urls: dict[str, tuple[type[Resource], str | None]] = {}
        self.__openapi_urls: dict[str, type[Resource]] = {}

    def add_url(self, path: str, resource: type[Resource], name: str | None = None):
        if not path.startswith("/"):
            raise ValueError("Path must start with '/'")

        p1, p2 = _convert_path(path)
        self.__django_urls[p1] = (resource, name)
        self.__openapi_urls[p2] = resource

    @property
    def urls(self):
        from django.urls import path

        return [
            path(django_path[1:], resource.as_view(), name=cast(str, name))
            for django_path, (resource, name) in self.__django_urls.items()
        ]

    def spec(self, openapi: str):
        return {
            path: resource.spec(openapi)
            for path, resource in self.__openapi_urls.items()
        }


def _convert_path(path: str) -> tuple[str, str]:
    """
    >>> _convert_path("/users/{id}")
    ('/users/<id>', '/users/{id}')

    >>> _convert_path("/users/{id}/{name}")
    ('/users/<id>/<name>', '/users/{id}/{name}')

    >>> _convert_path("/files/{path:file}")
    ('/files/<path:file>', '/files/{file}')

    >>> _convert_path("/users/{int:id}")
    Traceback (most recent call last):
    ...
    ValueError: Invalid path templating type: int
    """
    pattern = re.compile(r"\{(\w+(?::\w+)?)\}")

    def django_replace(match):
        param = match.group(1)
        if ":" in param:
            type, _ = param.split(":", 1)
            if type != "path":
                raise ValueError(f"Invalid path templating type: {type}")
        return f"<{param}>"

    def openapi_replace(match):
        param = match.group(1)
        if ":" in param:
            _, name = param.split(":", 1)
            return f"{{{name}}}"
        return f"{{{param}}}"

    return (
        re.sub(pattern, django_replace, path),
        re.sub(pattern, openapi_replace, path),
    )


class _ResponseDescription(NamedTuple):
    status: int
    content_type: str
    media_type: MediaType


_response_descriptions: ContextVar[list[_ResponseDescription]] = ContextVar(
    "response_descriptions"
)


def responseify(raw, /, *, status: int | None = None, content_type: str | None = None):
    descriptions = _response_descriptions.get([])

    # filter by status and content_type
    if status is not None:
        descriptions = filter(lambda x: x[0] == status, descriptions)
    if content_type is not None:
        descriptions = filter(lambda x: x[1] == content_type, descriptions)

    descriptions = list(descriptions)
    length = len(descriptions)
    if length > 1:
        raise RuntimeError(f"Multiple {MediaType.__name__} found")
    elif length == 0:
        raise RuntimeError(f"No {MediaType.__name__} found")

    d = descriptions[0]
    return import_string(
        ChainMap(
            settings.user_settings.OASIS_RESPONSE_CONTENT_PROCESSORS,
            settings.OASIS_RESPONSE_CONTENT_PROCESSORS,
        )[d.content_type]
    )(
        dict(
            data=d.media_type.parse(raw),
            status=d.status,
        )
    )


def _process_schema_parsing_exception(e: z.ValidationError, location: str):
    content = {
        "in": location,
        "errors": e.format_errors(),
    }
    return JsonResponse(content, status=422)


def _set_param(param: RequestParameterObject):
    def decorator(func):
        set_oas_definition(func, param)

        @functools.wraps(func)
        def wrapper(res, request, *args, **kwargs):
            try:
                extra = param.parse_request(request)
            except z.ValidationError as e:
                return _process_schema_parsing_exception(e, param.location)
            args, kwargs = param.modify_args(*args, **kwargs)
            return func(res, request, *args, **kwargs, **extra)

        return wrapper

    return decorator


class RequestBodyObject:
    def __init__(
        self,
        content: dict[str, MediaType],
        required: bool,
        description: str | None,
    ) -> None:
        self.__description = description
        self.content = content
        self.__required = required

    def spec(self, openapi: str):
        rv: dict = {
            "content": {k: v.spec(openapi) for k, v in self.content.items()},
        }
        if self.__description is not None:
            rv["description"] = self.__description
        if self.__required:
            rv["required"] = self.__required
        return rv


class Query(RequestParameterObject):
    location = "query"

    def get_argumentset(self, request):
        return request.GET


class Path(RequestParameterObject):
    location = "path"

    def get_argumentset(self, request: HttpRequest):
        return request.resolver_match.kwargs  # type: ignore

    def modify_args(self, *args, **kwargs):
        del kwargs[self.name]  # remove original path param
        return args, kwargs


class Cookie(RequestParameterObject):
    location = "cookie"

    def get_argumentset(self, request):
        return request.COOKIES


class Header(RequestParameterObject):
    location = "header"

    def get_argumentset(self, request):
        return request.headers


def path(*args, **kwargs):
    return _set_param(Path(*args, **kwargs))


def query(*args, **kwargs):
    return _set_param(Query(*args, **kwargs))


def cookie(*args, **kwargs):
    return _set_param(Cookie(*args, **kwargs))


def header(*args, **kwargs):
    return _set_param(Header(*args, **kwargs))


def body(
    bind_to: str,
    *,
    content: dict[str, MediaType],
    description: str | None = None,
    required=True,
):
    req_body = RequestBodyObject(
        content=content, description=description, required=required
    )

    def decorator(func):
        set_oas_definition(func, req_body)

        @functools.wraps(func)
        def wrapper(res, request: HttpRequest, *args, **kwargs):
            if request.content_type not in req_body.content:
                return HttpResponse(status=415)

            data_or_resp = import_string(
                ChainMap(
                    settings.user_settings.OASIS_REQUEST_CONTENT_PROCESSORS,
                    settings.OASIS_REQUEST_CONTENT_PROCESSORS,
                )[request.content_type]
            )(request)
            if isinstance(data_or_resp, HttpResponseBase):
                return data_or_resp

            media_type = req_body.content[request.content_type]
            try:
                value = media_type.parse(data_or_resp)
            except z.ValidationError as e:
                return _process_schema_parsing_exception(e, "body")
            extra = {bind_to: value}
            return func(res, request, *args, **kwargs, **extra)

        return wrapper

    return decorator


def response(
    status: int,
    /,
    *,
    content: dict[str, MediaType] | None = None,
    description: str | None = None,
):
    def decorator(func):
        set_oas_definition(func, ResponseObject(status, content, description))

        local = (
            [
                _ResponseDescription(status, content_type, media_type)
                for content_type, media_type in content.items()
            ]
            if content
            else []
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = _response_descriptions.set(local + _response_descriptions.get([]))
            try:
                return func(*args, **kwargs)
            finally:
                _response_descriptions.reset(token)

        return wrapper

    return decorator
