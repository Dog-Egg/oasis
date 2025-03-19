from django_oasis import Router

from .views import Login

router = Router()
router.add_url("/login", Login)
