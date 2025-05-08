from __future__ import annotations

import json

import zangar as z
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBase
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


def _process_schema_parsing_exception(e: z.ValidationError, location: str):
    content = {
        "in": location,
        "errors": e.format_errors(),
    }
    return JsonResponse(content, status=422)


class ParameterDecorator(ParameterDecoratorBase):
    def process_schema_parsing_exception(self, e: z.ValidationError):
        return _process_schema_parsing_exception(e, self.param.location)


def _json_response_processor(kwargs):
    return JsonResponse(kwargs["data"], status=kwargs["status"])


def _json_request_processor(request: HttpRequest):
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400, content_type="text/plain")


def _form_request_processor(request: HttpRequest):
    return request.POST.dict()


def _text_response_processor(kwargs):
    return HttpResponse(
        kwargs["data"], status=kwargs["status"], content_type="text/plain"
    )


class Resource(ResourceBase):
    request_content_processors = {
        "application/json": _json_request_processor,
        "application/x-www-form-urlencoded": _form_request_processor,
    }
    response_content_processors = {
        "application/json": _json_response_processor,
        "text/plain": _text_response_processor,
    }

    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        if method in HTTP_METHODS and hasattr(self, method):
            return getattr(self, method)(request, *args, **kwargs)
        return HttpResponse(status=405)

    @classmethod
    def as_view(cls):
        @catch_throw
        def view(*args, **kwargs):
            # 每个请求都会创建一个新的 Resoruce 实例，这意味即使将数据写入 self 也是安全的。
            with resource_ctx(cls):
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


class PathTemplate(PathTemplateBase):
    @property
    def django_path(self):
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
        return "/".join(parts)
