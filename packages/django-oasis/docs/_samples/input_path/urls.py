from __future__ import annotations

from django.urls import path
from django_oasis import PathTemplate, Resource

from .views import Users

paths: dict[PathTemplate, type[Resource]] = {
    PathTemplate("/users/{uid}"): Users,
}

urlpatterns = [path(p.django_path, resource.as_view()) for p, resource in paths.items()]
