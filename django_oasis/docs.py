import hashlib

from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.template.loader import render_to_string


def swagger_ui(config: dict):
    def view(request: HttpRequest):
        content = render_to_string(
            "swagger-ui.html",
            context=dict(
                config=config,
            ),
        )
        etag = '"%s"' % hashlib.sha1(content.encode()).hexdigest()
        if request.headers.get("If-None-Match") == etag:
            return HttpResponseNotModified()
        return HttpResponse(content, headers={"ETag": etag})

    return view
