from django_oasis import Router

from . import views

router = Router()
router.add_url("/MyAPI", views.MyAPI)
