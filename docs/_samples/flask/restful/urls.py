from flask_oasis import Router

from . import views

router = Router()
router.add_url("/users", views.UsersAPI)
router.add_url("/users/{uid}", views.UserAPI)
