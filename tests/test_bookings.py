from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient


def get_future_times() -> tuple[str, str]:
    future = datetime.now(UTC) + timedelta(days=1)
    start = future.replace(hour=14, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)
    return start.isoformat(), end.isoformat()


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["hall_id"] == test_hall["id"]
    assert data["status"] == "confirmed"
    assert len(data["seats"]) == 1


@pytest.mark.asyncio
async def test_create_booking_unauthorized(
    client: AsyncClient,
    test_hall: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_booking_hall_not_found(
    client: AsyncClient,
    auth_headers: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": 9999,
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookings(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/api/v1/bookings/",
        params={"page": 1, "page_size": 20},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_booking(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    create_response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


@pytest.mark.asyncio
async def test_cancel_booking(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
    test_seat: dict,
) -> None:
    start_time, end_time = get_future_times()

    create_response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_availability(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
) -> None:
    tomorrow = date.today() + timedelta(days=1)

    response = await client.get(
        f"/api/v1/bookings/halls/{test_hall['id']}/availability",
        params={"date": tomorrow.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_booking_invalid_duration(
    client: AsyncClient,
    auth_headers: dict,
    test_hall: dict,
    test_seat: dict,
) -> None:
    future = datetime.now(UTC) + timedelta(days=1)
    start = future.replace(hour=14, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": test_hall["id"],
            "seat_ids": [test_seat["id"]],
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
