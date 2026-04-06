import argparse
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db import async_session_maker
from app.models import User
from app.models.enums import UserRole


async def create_admin(email: str, password: str) -> None:
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            existing_user.role = UserRole.admin
            existing_user.is_active = True
            await db.commit()
            print(f"User {email} updated to admin role")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.admin,
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print("Admin created successfully!")
        print(f"Email: {email}")
        print(f"Role: {user.role.value}")


def main():
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password))


if __name__ == "__main__":
    main()
