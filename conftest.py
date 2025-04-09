import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_django():
    try:
        from django import setup
        from django.conf import settings
    except ImportError:  # pragma: no cover
        return

    settings.configure(
        INSTALLED_APPS=[
            "django_oasis",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            },
        ],
    )
    setup()
