from __future__ import annotations

from collections import ChainMap

import zangar as z
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBase
from django.utils.module_loading import import_string
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

from . import settings


def _process_schema_parsing_exception(e: z.ValidationError, location: str):
    content = {
        "in": location,
        "errors": e.format_errors(),
    }
    return JsonResponse(content, status=422)


class ParameterDecorator(ParameterDecoratorBase):
    def process_schema_parsing_exception(self, e: z.ValidationError):
        return _process_schema_parsing_exception(e, self.param.location)


class Resource(ResourceBase):
    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        if method in HTTP_METHODS and hasattr(self, method):
            return getattr(self, method)(request, *args, **kwargs)
        return HttpResponse(status=405)

    @classmethod
    def as_view(cls):
        def view(*args, **kwargs):
            # 每个请求都会创建一个新的 Resoruce 实例，这意味即使将数据写入 self 也是安全的。
            return cls().dispatch(*args, **kwargs)

        return view


class Query(QueryBase):
    def get_argumentset(self, request, *args, **kwargs):
        return request.GET


class Path(PathBase):
    def get_argumentset(self, request: HttpRequest, *args, **kwargs):
        return request.resolver_match.kwargs  # type: ignore

    def modify_args(self, *args, **kwargs):
        del kwargs[self.name]  # remove original path param
        return args, kwargs


class Cookie(CookieBase):
    def get_argumentset(self, request, *args, **kwargs):
        return request.COOKIES


class Header(HeaderBase):
    def get_argumentset(self, request, *args, **kwargs):
        return request.headers


def query(*args, **kwargs):
    return ParameterDecorator(Query(*args, **kwargs))


def path(*args, **kwargs):
    return ParameterDecorator(Path(*args, **kwargs))


def cookie(*args, **kwargs):
    return ParameterDecorator(Cookie(*args, **kwargs))


def header(*args, **kwargs):
    return ParameterDecorator(Header(*args, **kwargs))


class RequestBodyDecorator(RequestBodyDecoratorBase):
    def request_media_type(self, request: HttpRequest, *args, **kwargs):
        return request.content_type

    def get_processor(self, media_type):
        return import_string(
            ChainMap(
                settings.user_settings.OASIS_REQUEST_CONTENT_PROCESSORS,
                settings.OASIS_REQUEST_CONTENT_PROCESSORS,
            )[media_type]
        )

    def get_processor_args(self, request, *args, **kwargs) -> tuple:
        return (request,)

    def is_response(self, response):
        return isinstance(response, HttpResponseBase)

    def process_schema_parsing_exception(self, e: z.ValidationError):
        return _process_schema_parsing_exception(e, "body")

    def unsupported_media_type(self):
        return HttpResponse(status=415)


def body(*args, **kwargs):
    return RequestBodyDecorator(*args, **kwargs)


class Router(RouterBase):
    @property
    def urls(self):
        from django.urls import path

        rv = []
        for item in self._items:
            routes: list[str] = []
            for part in item.split_path:
                if isinstance(part, str):
                    routes.append(part)
                else:
                    routes.append(
                        f"<{part.variable}>"
                        if part.converter is None
                        else f"<{part.converter}:{part.variable}>"
                    )
            rv.append(path("/".join(routes), item.resource.as_view()))
        return rv


def responseify(*args, **kwargs):
    return responseify_base(
        *args,
        **kwargs,
        get_processor=lambda content_type: import_string(
            ChainMap(
                settings.user_settings.OASIS_RESPONSE_CONTENT_PROCESSORS,
                settings.OASIS_RESPONSE_CONTENT_PROCESSORS,
            )[content_type]
        ),
    )
