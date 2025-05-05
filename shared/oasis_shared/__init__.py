from __future__ import annotations

import abc
import contextlib
import functools
import itertools
import re
import warnings
from collections.abc import Callable, Hashable
from contextvars import ContextVar
from dataclasses import dataclass
from http import HTTPStatus
from inspect import iscoroutinefunction
from typing import Any, NamedTuple

import zangar as z

HTTP_METHODS = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]


class ResourceBase:
    def dispatch(self, *args, **kwargs):
        raise NotImplementedError

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

        for method in HTTP_METHODS:
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

    def parse_request(self, *args, **kwargs):
        argumentset = self.get_argumentset(*args, **kwargs)
        if isinstance(self.__schema, (z.struct, z.dataclass)):
            argumentset = {self.name: argumentset}

        field = z.field(self.__schema)
        if not self.__required:
            field = field.optional()
        return z.struct({self.name: field}).parse(argumentset)

    def get_argumentset(self, *args, **kwargs):
        raise NotImplementedError(self)

    def modify_args(self, *args, **kwargs):
        return args, kwargs


class QueryBase(RequestParameterObject):
    location = "query"


class HeaderBase(RequestParameterObject):
    location = "header"


class CookieBase(RequestParameterObject):
    location = "cookie"


class PathBase(RequestParameterObject):
    location = "path"


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


@dataclass
class _DynamicPart:
    converter: str | None
    variable: str


_part_re = re.compile(r"^\{(?:(?P<converter>[^:]+):)?(?P<variable>[^}]+)\}$")


def _split_path(path: str):
    if not path.startswith("/"):
        raise ValueError("path must start with '/'")
    parts: list[_DynamicPart | str] = []
    for part in path.split("/")[1:]:
        match = _part_re.match(part)
        if match:
            parts.append(_DynamicPart(**match.groupdict()))
        else:
            parts.append(part)
    return parts


class PathTemplateBase:
    def __init__(self, path: str, /) -> None:
        self._parts = _split_path(path)

    @property
    def openapi_path(self):
        parts: list[str] = []
        for part in self._parts:
            if isinstance(part, str):
                parts.append(part)
            else:
                parts.append(f"{{{part.variable}}}")
        return "/" + "/".join(parts)


class ResponseDefinition(NamedTuple):
    status: int
    media_type: str
    media_type_object: MediaType


response_definitions: ContextVar[list[ResponseDefinition]] = ContextVar(
    "response_definitions"
)


def responseify_base(
    raw,
    /,
    *,
    status: int | None = None,
    media_type: str | None = None,
    content_type: str | None = None,
    get_processor: Callable[[str], Callable],
):
    descriptions = response_definitions.get([])

    # filter by status and media_type
    if status is not None:
        descriptions = filter(lambda x: x.status == status, descriptions)

    if content_type is not None:
        warnings.warn(
            "content_type is deprecated, use media_type instead",
            DeprecationWarning,
            stacklevel=3,
        )
    if media_type is None:
        media_type = content_type

    if media_type is not None:
        descriptions = filter(lambda x: x.media_type == media_type, descriptions)

    descriptions = list(descriptions)
    length = len(descriptions)
    if length > 1:
        raise RuntimeError(f"Multiple {MediaType.__name__} found")
    elif length == 0:
        raise RuntimeError(f"No {MediaType.__name__} found")

    d = descriptions[0]
    return get_processor(d.media_type)(
        dict(
            data=d.media_type_object.parse(raw),
            status=d.status,
        )
    )


class ParameterDecoratorBase(abc.ABC):
    def __init__(self, param: RequestParameterObject):
        self.param = param

    def __call__(self, func):
        set_oas_definition(func, self.param)

        @functools.wraps(func)
        def wrapper(res, *args, **kwargs):
            try:
                extra = self.param.parse_request(*args, **kwargs)
            except z.ValidationError as e:
                return self.process_schema_parsing_exception(e)
            args, kwargs = self.param.modify_args(*args, **kwargs)
            return func(res, *args, **kwargs, **extra)

        return wrapper

    @abc.abstractmethod
    def process_schema_parsing_exception(self, e: z.ValidationError): ...


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
                ResponseDefinition(status, content_type, media_type)
                for content_type, media_type in content.items()
            ]
            if content
            else []
        )

        @contextlib.contextmanager
        def response_definitions_context():
            token = response_definitions.set(local + response_definitions.get([]))
            try:
                yield
            finally:
                response_definitions.reset(token)

        if iscoroutinefunction(func):

            @functools.wraps(func)
            async def awrapper(*args, **kwargs):
                with response_definitions_context():
                    return await func(*args, **kwargs)

            return awrapper
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with response_definitions_context():
                    return func(*args, **kwargs)

            return wrapper

    return decorator


class RequestBodyDecoratorBase(abc.ABC):
    def __init__(
        self,
        bind_to: str,
        /,
        *,
        content: dict[str, MediaType],
        description: str | None = None,
        required=True,
    ):
        self.request_body_object = RequestBodyObject(
            content=content, description=description, required=required
        )
        self.bind_to = bind_to

    def __call__(self, func):
        set_oas_definition(func, self.request_body_object)

        def get_media_type(*args, **kwargs):
            meida_type = self.request_media_type(*args, **kwargs)
            if meida_type not in self.request_body_object.content:
                throw(self.unsupported_media_type())
            return meida_type

        def parse_data(media_type: str, data):
            try:
                value = self.request_body_object.content[media_type].parse(data)
            except z.ValidationError as e:
                throw(self.process_schema_parsing_exception(e))
            return value

        if iscoroutinefunction(func):

            @functools.wraps(func)
            async def awrapper(res, *args, **kwargs):
                media_type = get_media_type(*args, **kwargs)
                processor = self.get_processor(media_type)
                processor_args = self.get_processor_args(*args, **kwargs)
                data = await processor(*processor_args)
                value = parse_data(media_type, data)
                return await func(res, *args, **kwargs, **{self.bind_to: value})

            return awrapper
        else:

            @functools.wraps(func)
            def wrapper(res, *args, **kwargs):
                media_type = get_media_type(*args, **kwargs)
                processor = self.get_processor(media_type)
                processor_args = self.get_processor_args(*args, **kwargs)
                data = processor(*processor_args)
                if self.is_response(data):
                    return data
                value = parse_data(media_type, data)
                return func(res, *args, **kwargs, **{self.bind_to: value})

            return wrapper

    def get_processor_args(self, *args, **kwargs) -> tuple:
        return tuple()

    @abc.abstractmethod
    def request_media_type(self, *args, **kwargs) -> str: ...

    @abc.abstractmethod
    def unsupported_media_type(self): ...

    def is_response(self, response):
        raise NotImplementedError

    @abc.abstractmethod
    def get_processor(self, media_type: str) -> Callable: ...

    @abc.abstractmethod
    def process_schema_parsing_exception(self, e: z.ValidationError): ...


class ThrowValue(Exception):
    def __init__(self, value):
        self.value = value


def throw(value, /):
    raise ThrowValue(value)


def catch_throw(func):
    if iscoroutinefunction(func):

        @functools.wraps(func)
        async def awrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ThrowValue as e:
                return e.value

        return awrapper
    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ThrowValue as e:
                return e.value

        return wrapper
