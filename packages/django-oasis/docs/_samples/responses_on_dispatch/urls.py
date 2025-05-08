from django_oasis import PathTemplate

from .views import Greeting

paths = {
    PathTemplate("/Greeting"): Greeting,
}
