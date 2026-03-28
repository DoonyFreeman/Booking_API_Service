from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class BookingStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
