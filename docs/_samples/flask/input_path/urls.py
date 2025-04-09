from flask_oasis import Router

from .views import Users

router = Router()
router.add_url("/users/{uid}", Users)
