import json

from django.http import HttpRequest, HttpResponse, JsonResponse


def json_response_processor(kwargs):
    return JsonResponse(kwargs["data"], status=kwargs["status"])


def json_request_processor(request: HttpRequest):
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400, content_type="text/plain")


def form_request_processor(request: HttpRequest):
    return request.POST.dict()


def text_response_processor(kwargs):
    return HttpResponse(
        kwargs["data"], status=kwargs["status"], content_type="text/plain"
    )
