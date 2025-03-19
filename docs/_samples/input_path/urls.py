from django.urls import include, path
from django_oasis import Router

from .views import Users

router = Router()
router.add_url("/users/{uid}", Users)

urlpatterns = [
    path("", include(router.urls)),
]
