from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from app.modules.authentication.models import UserRole
from app.modules.authentication.schemas import UserResponse


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserInviteRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.MEMBER


class UserInviteResponse(BaseModel):
    message: str
    email: str
    role: UserRole
    organization_id: str


class UserAcceptInvitationRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int