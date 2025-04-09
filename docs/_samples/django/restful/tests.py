from django.test import Client, override_settings

from . import urls


class TestRESTful:
    client = Client()

    @classmethod
    def setup_class(cls):
        cls.settings = override_settings(ROOT_URLCONF=urls)
        cls.settings.enable()

    @classmethod
    def teardown_class(cls):
        cls.settings.disable()

    def test_users_get(self):
        response = self.client.get("/users")
        assert response.status_code == 200
        assert response.json() == {
            "users": [
                {"id": 1, "name": "James"},
                {"id": 2, "name": "Linda"},
                {"id": 3, "name": "Emily"},
            ],
            "page": 1,
            "page_size": 10,
        }

    def test_users_get_page(self):
        response = self.client.get("/users?page=2&page_size=1")
        assert response.json() == {
            "users": [{"id": 2, "name": "Linda"}],
            "page": 2,
            "page_size": 1,
        }

    def test_users_post(self):
        response = self.client.post(
            "/users", {"name": "Tom"}, content_type="application/json"
        )
        assert response.status_code == 201
        assert response.json() == {"id": 4, "name": "Tom"}

    def test_user_get(self):
        response = self.client.get("/users/1")
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "James"}

    def test_user_patch(self):
        response = self.client.patch(
            "/users/1", {"name": "Tom"}, content_type="application/json"
        )
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "Tom"}

    def test_user_delete(self):
        response = self.client.delete("/users/1")
        assert response.status_code == 204
