from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
