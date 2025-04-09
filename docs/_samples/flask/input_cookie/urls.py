from flask_oasis import Router

from .views import MyAPI

router = Router()
router.add_url("/myapi", MyAPI)
