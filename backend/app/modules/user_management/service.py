from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.user_management.repository import UserManagementRepository
from app.modules.user_management.models import UserInvitation
from app.modules.authentication.models import User, UserRole
from app.modules.user_management.schemas import UserInviteRequest, UserInviteResponse, UserRoleUpdate, UserResponse
from app.modules.authentication.service import AuthService
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, BusinessRuleViolationException
from app.shared.logging.logger import app_logger
from app.shared.security.password import hash_password
import secrets
from datetime import datetime, timedelta


class UserManagementService:
    def __init__(self, session: AsyncSession):
        self.repo = UserManagementRepository(session)
        self.auth_service = AuthService(session)

    async def invite_user(self, organization_id: UUID, invited_by: UUID, request: UserInviteRequest) -> UserInviteResponse:
        existing_user = await self.auth_service.repo.get_by_email(request.email)
        if existing_user and existing_user.organization_id == organization_id:
            raise ValidationException("User already exists in this organization")

        existing_invitation = await self.repo.get_invitation_by_email(organization_id, request.email)
        if existing_invitation:
            raise ValidationException("Invitation already sent to this email")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = UserInvitation(
            email=request.email,
            role=request.role,
            token=token,
            expires_at=expires_at,
            organization_id=organization_id,
            invited_by=invited_by,
        )
        invitation = await self.repo.create_invitation(invitation)

        app_logger.info(f"User invited", extra={"email": request.email, "organization_id": str(organization_id)})
        return UserInviteResponse.model_validate(invitation)

    async def accept_invitation(self, token: str, password: str, full_name: str) -> UserResponse:
        invitation = await self.repo.get_invitation_by_token(token)
        if not invitation:
            raise ResourceNotFoundException("Invalid invitation token")

        if invitation.accepted_at:
            raise ValidationException("Invitation already accepted")

        if invitation.expires_at < datetime.utcnow():
            raise ValidationException("Invitation has expired")

        existing_user = await self.auth_service.repo.get_by_email(invitation.email)
        if existing_user:
            raise ValidationException("User with this email already exists")

        user = User(
            email=invitation.email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=invitation.role,
            organization_id=invitation.organization_id,
        )
        user = await self.auth_service.repo.create(user)

        invitation.accepted_at = datetime.utcnow()
        await self.repo.update_invitation(invitation)

        app_logger.info(f"User accepted invitation", extra={"user_id": str(user.id)})
        return UserResponse.model_validate(user)

    async def list_users(self, organization_id: UUID, page: int = 1, page_size: int = 20) -> Tuple[List[UserResponse], int]:
        items, total = await self.repo.get_users_by_org(organization_id, page, page_size)
        return [UserResponse.model_validate(item) for item in items], total

    async def update_role(self, organization_id: UUID, user_id: UUID, request: UserRoleUpdate, current_user: User) -> UserResponse:
        if user_id == current_user.id:
            raise BusinessRuleViolationException("Cannot change your own role")

        target_user = await self.repo.get_user_by_id(user_id, organization_id)
        if not target_user:
            raise ResourceNotFoundException("User not found")

        if target_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise BusinessRuleViolationException("Cannot modify admin user")

        target_user.role = request.role
        await self.auth_service.repo.session.flush()
        await self.auth_service.repo.session.refresh(target_user)

        app_logger.info(f"User role updated", extra={"user_id": str(user_id), "new_role": request.role.value})
        return UserResponse.model_validate(target_user)

    async def deactivate_user(self, organization_id: UUID, user_id: UUID, current_user: User) -> None:
        if user_id == current_user.id:
            raise BusinessRuleViolationException("Cannot deactivate yourself")

        target_user = await self.repo.get_user_by_id(user_id, organization_id)
        if not target_user:
            raise ResourceNotFoundException("User not found")

        if target_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise BusinessRuleViolationException("Cannot deactivate admin user")

        target_user.is_active = False
        await self.auth_service.repo.session.flush()

        app_logger.info(f"User deactivated", extra={"user_id": str(user_id)})