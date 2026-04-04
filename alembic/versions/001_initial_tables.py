"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-03-28

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_role", "users", ["role"])

    # halls table
    op.create_table(
        "halls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_halls_name", "halls", ["name"])
    op.create_index("ix_halls_is_active", "halls", ["is_active"])

    # seats table
    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hall_id", sa.Integer(), nullable=False),
        sa.Column("row", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["hall_id"], ["halls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hall_id", "row", "number", name="uq_seat_position"),
    )
    op.create_index("ix_seats_hall_id", "seats", ["hall_id"])
    op.create_index("ix_seats_is_active", "seats", ["is_active"])

    # bookings table
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hall_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hall_id"], ["halls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_hall_id", "bookings", ["hall_id"])
    op.create_index("ix_bookings_start_time", "bookings", ["start_time"])
    op.create_index("ix_bookings_end_time", "bookings", ["end_time"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index(
        "ix_bookings_hall_time", "bookings", ["hall_id", "start_time", "end_time"]
    )

    # booking_seats table
    op.create_table(
        "booking_seats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("seat_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_booking_seats_booking_id", "booking_seats", ["booking_id"])
    op.create_index("ix_booking_seats_seat_id", "booking_seats", ["seat_id"])


def downgrade() -> None:
    op.drop_table("booking_seats")
    op.drop_table("bookings")
    op.drop_table("seats")
    op.drop_table("halls")
    op.drop_table("users")
