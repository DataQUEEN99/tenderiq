from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from app.modules.authentication.models import UserRole
from app.modules.authentication.schemas import UserResponse


class UserInviteRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.MEMBER


class UserInviteResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    expires_at: datetime
    organization_id: str
    invited_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserAcceptInvitationRequest(BaseModel):
    token: str
    password: str
    full_name: str


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int