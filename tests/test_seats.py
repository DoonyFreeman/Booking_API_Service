import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_seat_admin(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> None:
    response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["row"] == 1
    assert data["number"] == 1
    assert data["hall_id"] == test_hall["id"]


@pytest.mark.asyncio
async def test_create_seat_user_forbidden(
    client: AsyncClient, auth_headers: dict, test_hall: dict
) -> None:
    response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_duplicate_seat(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> None:
    await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=admin_headers,
    )

    response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_seats(
    client: AsyncClient, auth_headers: dict, admin_headers: dict, test_hall: dict
) -> None:
    await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=admin_headers,
    )
    await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 2},
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_bulk_create_seats(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> None:
    response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/bulk",
        json={
            "rows": 2,
            "seats_per_row": 5,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 10


@pytest.mark.asyncio
async def test_delete_seat(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> None:
    create_response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={"row": 1, "number": 1},
        headers=admin_headers,
    )
    seat_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/halls/{test_hall['id']}/seats/{seat_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204
