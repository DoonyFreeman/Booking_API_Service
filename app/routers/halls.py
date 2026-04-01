from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.exceptions import HallNotFoundError
from app.models import Hall, Seat
from app.schemas import HallCreate, HallResponse, HallUpdate

router = APIRouter(prefix="/halls", tags=["halls"])


@router.get("/", response_model=List[HallResponse])
async def list_halls(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> List[HallResponse]:
    result = await db.execute(
        select(Hall)
        .where(Hall.is_active == True)
        .options(selectinload(Hall.seats))
        .order_by(Hall.id)
    )
    halls = result.scalars().all()

    response = []
    for hall in halls:
        hall_data = HallResponse.model_validate(hall)
        hall_data.total_seats = len([s for s in hall.seats if s.is_active])
        hall_data.free_seats = hall_data.total_seats
        response.append(hall_data)

    return response


@router.get("/{hall_id}", response_model=HallResponse)
async def get_hall(
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> HallResponse:
    result = await db.execute(
        select(Hall).options(selectinload(Hall.seats)).where(Hall.id == hall_id)
    )
    hall = result.scalar_one_or_none()

    if not hall:
        raise HallNotFoundError()

    response = HallResponse.model_validate(hall)
    response.total_seats = len([s for s in hall.seats if s.is_active])
    response.free_seats = response.total_seats

    return response


@router.post(
    "/",
    response_model=HallResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hall(
    data: HallCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> HallResponse:
    hall = Hall(
        name=data.name,
        capacity=data.capacity,
        hourly_rate=data.hourly_rate,
        is_active=True,
    )

    db.add(hall)
    await db.flush()
    await db.refresh(hall)

    return HallResponse.model_validate(hall)


@router.patch("/{hall_id}", response_model=HallResponse)
async def update_hall(
    hall_id: int,
    data: HallUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> HallResponse:
    result = await db.execute(
        select(Hall).options(selectinload(Hall.seats)).where(Hall.id == hall_id)
    )
    hall = result.scalar_one_or_none()

    if not hall:
        raise HallNotFoundError()

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hall, field, value)

    await db.flush()
    await db.refresh(hall)

    response = HallResponse.model_validate(hall)
    response.total_seats = len([s for s in hall.seats if s.is_active])
    response.free_seats = response.total_seats

    return response


@router.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hall(
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> None:
    result = await db.execute(select(Hall).where(Hall.id == hall_id))
    hall = result.scalar_one_or_none()

    if not hall:
        raise HallNotFoundError()

    hall.is_active = False
    await db.flush()
