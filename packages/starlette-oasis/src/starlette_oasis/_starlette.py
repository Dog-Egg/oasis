from contextvars import ContextVar

import zangar as z
from oasis_shared import (
    HTTP_METHODS,
    ParameterDecoratorBase,
    PathBase,
    PathTemplateBase,
    QueryBase,
    RequestBodyDecoratorBase,
    ResourceBase,
    catch_throw,
    resource_ctx,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Receive, Scope, Send

_request_cv: ContextVar[Request] = ContextVar("request")


async def _json_request_processor(request: Request):
    return await request.json()


def _json_response_processor(kwargs):
    return JSONResponse(kwargs["data"], status_code=kwargs["status"])


class Resource(ResourceBase):
    request_content_processors = {
        "application/json": _json_request_processor,
    }
    response_content_processors = {
        "application/json": _json_response_processor,
    }

    def __init__(self, scope: Scope, receive: Receive, send: Send):
        self.__scope = scope
        self.__receive = receive
        self.__send = send

    async def dispatch(self, request: Request, *args, **kwargs):
        method = request.method.lower()
        if method in HTTP_METHODS and hasattr(self, method):
            handle = getattr(self, method)
            response = await handle(request, *args, **kwargs)
        else:
            response = Response(status_code=405)
        return response

    def __await__(self):
        async def func():
            request = Request(self.__scope, receive=self.__receive)
            token = _request_cv.set(request)
            with resource_ctx(self.__class__):
                try:
                    response = await catch_throw(self.dispatch)(request)
                finally:
                    _request_cv.reset(token)
            await response(self.__scope, self.__receive, self.__send)

        return func().__await__()


class Query(QueryBase):
    def get_argumentset(self, request: Request, *args, **kwargs):
        return request.query_params


class ParameterDecorator(ParameterDecoratorBase):
    def process_schema_parsing_exception(self, e: z.ValidationError):
        return _process_schema_parsing_exception(e, self.param.location)


def _process_schema_parsing_exception(e: z.ValidationError, location: str):
    return JSONResponse({"in": location, "errors": e.format_errors()}, 422)


def query(*args, **kwargs):
    return ParameterDecorator(Query(*args, **kwargs))


class RequestBodyDecorator(RequestBodyDecoratorBase):
    def process_schema_parsing_exception(self, e: z.ValidationError):
        return _process_schema_parsing_exception(e, "body")

    def request_media_type(self, request: Request, *args, **kwargs):
        return request.headers.get("content-type")

    def unsupported_media_type(self):
        return Response(status_code=415)

    def get_processor_args(self, request, *args, **kwargs):
        return (request,)


def body(*args, **kwargs):
    return RequestBodyDecorator(*args, **kwargs)


class Path(PathBase):
    def get_argumentset(self, request: Request):
        return request.path_params


def path(*args, **kwargs):
    return ParameterDecorator(Path(*args, **kwargs))


class PathTemplate(PathTemplateBase):
    @property
    def starlette_path(self):
        parts = []
        for part in self._parts:
            if isinstance(part, str):
                parts.append(part)
            else:
                parts.append(
                    f"{{{part.variable}}}"
                    if part.converter is None
                    else f"{{{part.variable}:{part.converter}}}"
                )
        return "/" + "/".join(parts)
