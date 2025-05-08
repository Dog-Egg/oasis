import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from .app import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_users_get(client):
    response = await client.get("/users")
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


@pytest.mark.asyncio
async def test_users_get_page(client):
    response = await client.get("/users?page=2&page_size=1")
    assert response.json() == {
        "users": [{"id": 2, "name": "Linda"}],
        "page": 2,
        "page_size": 1,
    }


@pytest.mark.asyncio
async def test_users_post(client):
    response = await client.post("/users", json={"name": "Tom"})
    assert response.status_code == 201
    assert response.json() == {"id": 4, "name": "Tom"}


@pytest.mark.asyncio
async def test_user_get(client):
    response = await client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "James"}


@pytest.mark.asyncio
async def test_user_patch(client):
    response = await client.patch("/users/1", json={"name": "Tom"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Tom"}


@pytest.mark.asyncio
async def test_user_delete(client):
    response = await client.delete("/users/1")
    assert response.status_code == 204
