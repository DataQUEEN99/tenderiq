from datetime import timedelta
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.authentication.repository import AuthRepository
from app.modules.authentication.models import User, UserRole
from app.modules.organization.models import Organization, OrganizationStatus
from app.modules.authentication.schemas import (
    LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest,
    BootstrapRequest, BootstrapResponse
)
from app.shared.security.jwt import create_access_token
from app.shared.security.password import hash_password, verify_password
from app.shared.exceptions.custom_exceptions import AuthenticationException, ValidationException, ResourceNotFoundException
from app.shared.logging.logger import app_logger


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = AuthRepository(session)
        self.session = session

    async def bootstrap(self, request: BootstrapRequest) -> BootstrapResponse:
        # Check if any admin/user already exists
        user_count = await self.repo.count_users()
        if user_count > 0:
            raise ValidationException("System has already been bootstrapped with existing users.")

        # Create the first organization
        slug = request.organization_slug or re.sub(r'[^a-zA-Z0-9]', '-', request.organization_name.lower()).strip('-')
        org = Organization(
            name=request.organization_name,
            slug=slug,
            status=OrganizationStatus.ACTIVE,
            is_deleted=False
        )
        self.session.add(org)
        await self.session.flush()
        await self.session.refresh(org)

        # Create root admin user
        admin_user = User(
            email=request.admin_email,
            password_hash=hash_password(request.admin_password),
            full_name=request.admin_full_name,
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=org.id
        )
        self.session.add(admin_user)
        await self.session.flush()
        await self.session.refresh(admin_user)

        token = self.create_token(admin_user)
        app_logger.info(f"System bootstrapped successfully", extra={"organization_id": str(org.id), "admin_email": request.admin_email})

        return BootstrapResponse(
            message="System bootstrapped successfully",
            organization_id=str(org.id),
            user_id=str(admin_user.id),
            access_token=token,
            token_type="bearer"
        )

    async def login(self, request: LoginRequest) -> LoginResponse:
        user = await self.repo.get_by_email(request.email)
        if not user:
            app_logger.warning(f"Login failed: user not found", extra={"email": request.email})
            raise AuthenticationException("Invalid credentials")

        if not user.is_active:
            raise AuthenticationException("Account is deactivated")

        if not verify_password(request.password, user.password_hash):
            app_logger.warning(f"Login failed: invalid password", extra={"email": request.email})
            raise AuthenticationException("Invalid credentials")

        token_data = {
            "sub": str(user.id),
            "organization_id": str(user.organization_id),
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)

        return LoginResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    async def get_current_user(self, user_id: str) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        return UserResponse.model_validate(user)

    async def change_password(self, user_id: str, request: ChangePasswordRequest) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")

        if not verify_password(request.current_password, user.password_hash):
            raise ValidationException("Current password is incorrect")

        user.password_hash = hash_password(request.new_password)
        await self.repo.session.flush()
        app_logger.info(f"Password changed", extra={"user_id": user_id})

    def create_token(self, user: User) -> str:
        token_data = {
            "sub": str(user.id),
            "organization_id": str(user.organization_id),
            "role": user.role.value,
        }
        return create_access_token(token_data)