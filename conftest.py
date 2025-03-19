import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_django():
    from django import setup
    from django.conf import settings

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
