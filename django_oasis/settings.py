from typing import Any

DEFAULTS = {
    "OASIS_REQUEST_CONTENT_PROCESSORS": {},
    "OASIS_RESPONSE_CONTENT_PROCESSORS": {},
}

OASIS_REQUEST_CONTENT_PROCESSORS = {
    "application/json": "django_oasis.processors.json_request_processor",
    "application/x-www-form-urlencoded": "django_oasis.processors.form_request_processor",
}
OASIS_RESPONSE_CONTENT_PROCESSORS = {
    "application/json": "django_oasis.processors.json_response_processor",
    "text/plain": "django_oasis.processors.text_response_processor",
}


class _UserSettings:
    __wrapped__ = None

    def __getattr__(self, name) -> Any:
        from django.conf import settings as django_settings

        if hasattr(django_settings, name):
            return getattr(django_settings, name)

        try:
            return DEFAULTS[name]
        except KeyError:
            raise AttributeError(f"Settings has no attribute {name}")


#: The settings object
user_settings = _UserSettings()
