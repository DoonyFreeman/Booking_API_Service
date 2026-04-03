import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_halls_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/halls/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_halls_empty(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/halls/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_hall_admin(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.post(
        "/api/v1/halls/",
        json={
            "name": "Main Hall",
            "capacity": 100,
            "hourly_rate": 150.00,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Main Hall"
    assert data["capacity"] == 100
    assert data["hourly_rate"] == "150.00"


@pytest.mark.asyncio
async def test_create_hall_user_forbidden(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(
        "/api/v1/halls/",
        json={
            "name": "User Hall",
            "capacity": 50,
            "hourly_rate": 100.00,
        },
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_halls_with_data(
    client: AsyncClient, admin_headers: dict, auth_headers: dict
) -> None:
    await client.post(
        "/api/v1/halls/",
        json={
            "name": "Hall 1",
            "capacity": 50,
            "hourly_rate": 100.00,
        },
        headers=admin_headers,
    )

    response = await client.get("/api/v1/halls/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Hall 1"


@pytest.mark.asyncio
async def test_get_hall(
    client: AsyncClient, admin_headers: dict, auth_headers: dict, test_hall: dict
) -> None:
    response = await client.get(
        f"/api/v1/halls/{test_hall['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Hall"


@pytest.mark.asyncio
async def test_get_hall_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/halls/999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_hall(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> None:
    response = await client.patch(
        f"/api/v1/halls/{test_hall['id']}",
        json={"name": "Updated Hall", "hourly_rate": 200.00},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Hall"
    assert data["hourly_rate"] == "200.00"


@pytest.mark.asyncio
async def test_delete_hall(
    client: AsyncClient, admin_headers: dict, auth_headers: dict, test_hall: dict
) -> None:
    response = await client.delete(
        f"/api/v1/halls/{test_hall['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    response = await client.get("/api/v1/halls/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []
