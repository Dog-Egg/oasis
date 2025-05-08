from django_oasis import PathTemplate

from .views import MyAPI

paths = {
    PathTemplate("/MyAPI"): MyAPI,
}
