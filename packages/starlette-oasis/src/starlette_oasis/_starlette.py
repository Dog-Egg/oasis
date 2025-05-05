import importlib
from contextvars import ContextVar

from oasis_shared import (
    HTTP_METHODS,
    ParameterDecoratorBase,
    PathBase,
    PathTemplateBase,
    QueryBase,
    RequestBodyDecoratorBase,
    ResourceBase,
    catch_throw,
    responseify_base,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from zangar.exceptions import ValidationError

_request_cv: ContextVar[Request] = ContextVar("request")


class Resource(ResourceBase):
    def __init__(self, scope, receive, send) -> None:
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
            try:
                response = await catch_throw(self.dispatch)(request)
            finally:
                _request_cv.reset(token)
            await response(self.__scope, self.__receive, self.__send)

        return func().__await__()


def json_response_processor(kwargs):
    return JSONResponse(kwargs["data"], status_code=kwargs["status"])


DEFAULT_RESPONSE_CONTENT_PROCESSORS = {
    "application/json": json_response_processor,
}


def responseify(*args, **kwargs):
    def get_processor(media_type):
        request = _request_cv.get()
        try:
            processors = request.app.state.OASIS_RESPONSE_CONTENT_PROCESSORS
        except AttributeError:
            pass
        else:
            if media_type in processors:
                return import_string(processors[media_type])
        return DEFAULT_RESPONSE_CONTENT_PROCESSORS[media_type]

    return responseify_base(*args, **kwargs, get_processor=get_processor)


def import_string(import_name: str):
    try:
        module_name, obj_name = import_name.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"Invalid import path: {import_name}")
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


class Query(QueryBase):
    def get_argumentset(self, request: Request, *args, **kwargs):
        return request.query_params


class ParameterDecorator(ParameterDecoratorBase):
    def process_schema_parsing_exception(self, e: ValidationError):
        return _process_schema_parsing_exception(e, self.param.location)


def _process_schema_parsing_exception(e: ValidationError, location: str):
    return JSONResponse({"in": location, "errors": e.format_errors()}, 422)


def query(*args, **kwargs):
    return ParameterDecorator(Query(*args, **kwargs))


class RequestBodyDecorator(RequestBodyDecoratorBase):
    def process_schema_parsing_exception(self, e: ValidationError):
        return _process_schema_parsing_exception(e, "body")

    def request_media_type(self, request: Request, *args, **kwargs):
        return request.headers.get("content-type")

    def unsupported_media_type(self):
        return Response(status_code=415)

    def get_processor(self, media_type: str):
        async def json_request_processor(request: Request):
            return await request.json()

        return {
            "application/json": json_request_processor,
        }[media_type]

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
