import pytest
from fastapi.testclient import TestClient
from sqlmodel_fastapi import app
from httpx import ASGITransport, AsyncClient

client = TestClient(app)

def test_create_item():
    response = client.post("/items/", json={"name": "Test Item", "description": "Test Description"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "Test Description"
    assert "id" in data

def test_read_item():
    # First, create an item to read
    response = client.post("/items/", json={"name": "Read Item", "description": "Read Description"})
    assert response.status_code == 200
    item_id = response.json()["id"]

    # Now, read the item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == "Read Item"
    assert data["description"] == "Read Description"


@pytest.mark.asyncio
async def test_create_item_async():
    async with AsyncClient(app=app, transport=ASGITransport(app=app)) as client:
        response = await client.post("/items/", json={"name": "Async Test Item", "description": "Async Test Description"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Async Test Item"
        assert data["description"] == "Async Test Description"
        assert "id" in data

@pytest.mark.asyncio
async def test_read_item_async():
    async with AsyncClient(app=app, transport=ASGITransport(app=app)) as client:
        # First, create an item to read
        response = await client.post("/items/", json={"name": "Async Read Item", "description": "Async Read Description"})
        assert response.status_code == 200
        item_id = response.json()["id"]

        # Now, read the item
        response = await client.get(f"/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == "Async Read Item"
        assert data["description"] == "Async Read Description"