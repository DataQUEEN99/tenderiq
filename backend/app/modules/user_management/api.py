from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.session import get_db
from app.modules.user_management.service import UserManagementService
from app.modules.user_management.schemas import (
    UserRoleUpdate, UserListResponse, UserInviteRequest, UserInviteResponse
)
from app.modules.authentication.schemas import UserResponse
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_READ)),
):
    service = UserManagementService(db)
    items, total = await service.list_users(current_user.organization_id, page, page_size)
    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/invite", response_model=UserInviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    request: UserInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_INVITE)),
):
    service = UserManagementService(db)
    return await service.invite_user(current_user.organization_id, request, current_user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    request: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_ROLE)),
):
    service = UserManagementService(db)
    return await service.update_role(current_user.organization_id, user_id, request, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
):
    service = UserManagementService(db)
    await service.deactivate_user(current_user.organization_id, user_id, current_user)
