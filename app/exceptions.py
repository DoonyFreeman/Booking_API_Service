from fastapi import HTTPException, status


class BookingConflictError(HTTPException):
    def __init__(self, detail: str = "Booking conflict") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class BookingNotFoundError(HTTPException):
    def __init__(self, detail: str = "Booking not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class HallNotFoundError(HTTPException):
    def __init__(self, detail: str = "Hall not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class SeatNotFoundError(HTTPException):
    def __init__(self, detail: str = "Seat not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class UserNotFoundError(HTTPException):
    def __init__(self, detail: str = "User not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class InvalidTimeSlotError(HTTPException):
    def __init__(self, detail: str = "Invalid time slot") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Not authorized") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
