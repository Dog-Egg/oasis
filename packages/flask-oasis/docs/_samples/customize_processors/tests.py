import yaml

from .app import app


def test_requests():
    with app.test_client() as client:
        response = client.post(
            "/myapi",
            data=yaml.safe_dump({"name": "Tom", "age": 18}),
            content_type="application/yaml",
        )

        assert response.request.mimetype == "application/yaml"
        assert response.status_code == 200
        assert response.data == b"name: Tom\nage: 18\n"
        assert response.mimetype == "application/yaml"
