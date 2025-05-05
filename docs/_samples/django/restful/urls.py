from __future__ import annotations

from django.urls import path
from django_oasis import PathTemplate, Resource

from . import views

paths: dict[PathTemplate, type[Resource]] = {
    PathTemplate("/users"): views.UsersAPI,
    PathTemplate("/users/{uid}"): views.UserAPI,
}

urlpatterns = [path(p.django_path, resource.as_view()) for p, resource in paths.items()]
