from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.modules.authentication.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class TokenPayload(BaseModel):
    sub: str
    organization_id: str
    role: UserRole
    exp: int


class BootstrapRequest(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255)
    organization_slug: Optional[str] = None
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_full_name: str = Field(..., min_length=1, max_length=255)


class BootstrapResponse(BaseModel):
    message: str
    organization_id: str
    user_id: str
    access_token: str
    token_type: str = "bearer"