from enum import StrEnum


class UserRole(StrEnum):
    user = "user"
    admin = "admin"


class BookingStatus(StrEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"
