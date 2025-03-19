from django_oasis import Router

from .views import MyAPI

router = Router()

router.add_url("/MyAPI", MyAPI)
