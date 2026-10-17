from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.modules.authentication.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


from app.modules.organization.schemas import OrganizationResponse


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
    organization: Optional[OrganizationResponse] = None


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


class RegisterOrgRequest(BaseModel):
    org_name: Optional[str] = None
    organization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    admin_email: Optional[EmailStr] = None
    password: Optional[str] = None
    admin_password: Optional[str] = None
    full_name: Optional[str] = None
    admin_full_name: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None