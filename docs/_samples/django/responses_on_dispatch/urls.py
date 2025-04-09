from django_oasis import Router

from .views import Greeting

router = Router()
router.add_url("/Greeting", Greeting)
