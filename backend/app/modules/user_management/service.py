from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
import secrets
from app.modules.user_management.repository import UserManagementRepository
from app.modules.authentication.models import User, UserRole
from app.modules.user_management.schemas import (
    UserRoleUpdate, UserResponse, UserInviteRequest, UserInviteResponse
)
from app.modules.authentication.service import AuthService
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, BusinessRuleViolationException
from app.shared.logging.logger import app_logger
from app.shared.security.password import hash_password


class UserManagementService:
    def __init__(self, session: AsyncSession):
        self.repo = UserManagementRepository(session)
        self.auth_service = AuthService(session)

    async def list_users(self, organization_id: UUID, page: int = 1, page_size: int = 20) -> Tuple[List[UserResponse], int]:
        items, total = await self.repo.get_users_by_org(organization_id, page, page_size)
        return [UserResponse.model_validate(item) for item in items], total

    async def update_role(self, organization_id: UUID, user_id: UUID, request: UserRoleUpdate, current_user: User) -> UserResponse:
        if user_id == current_user.user_id:
            raise BusinessRuleViolationException("Cannot change your own role")

        target_user = await self.repo.get_user_by_id(user_id, organization_id)
        if not target_user:
            raise ResourceNotFoundException("User not found")

        if target_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise BusinessRuleViolationException("Cannot modify admin user")

        target_user.role = request.role
        await self.repo.update(target_user)

        app_logger.info(f"User role updated", extra={"user_id": str(user_id), "new_role": request.role.value})
        return UserResponse.model_validate(target_user)

    async def deactivate_user(self, organization_id: UUID, user_id: UUID, current_user: User) -> None:
        if user_id == current_user.user_id:
            raise BusinessRuleViolationException("Cannot deactivate yourself")

        target_user = await self.repo.get_user_by_id(user_id, organization_id)
        if not target_user:
            raise ResourceNotFoundException("User not found")

        if target_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise BusinessRuleViolationException("Cannot deactivate admin user")

        target_user.is_active = False
        await self.repo.update(target_user)

        app_logger.info(f"User deactivated", extra={"user_id": str(user_id)})

    async def invite_user(self, organization_id: UUID, request: UserInviteRequest, current_user: User) -> UserInviteResponse:
        """Invite a new user to the organization by creating them with a temporary password."""
        # Check if user already exists in this org
        existing = await self.repo.get_user_by_email_in_org(request.email, organization_id)
        if existing:
            raise ValidationException(f"User with email {request.email} already exists in this organization")

        # Generate temporary password
        temp_password = secrets.token_urlsafe(12)

        # Create user with temporary password
        new_user = User(
            email=request.email,
            password_hash=hash_password(temp_password),
            full_name=request.full_name,
            role=request.role,
            is_active=True,
            organization_id=organization_id,
        )
        new_user = await self.repo.create(new_user)

        # TODO: Send invitation email with temporary password
        # For now, return the temp password in response (in production, send via email)
        app_logger.info(f"User invited", extra={
            "user_id": str(new_user.user_id),
            "email": request.email,
            "organization_id": str(organization_id),
            "invited_by": str(current_user.user_id)
        })

        return UserInviteResponse(
            message="User invited successfully. Share the temporary password securely.",
            email=request.email,
            role=request.role,
            organization_id=str(organization_id)
        )