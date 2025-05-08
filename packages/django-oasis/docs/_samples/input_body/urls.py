from django_oasis import PathTemplate

from .views import Login

paths = {
    PathTemplate("/login"): Login,
}
