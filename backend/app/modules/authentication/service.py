from datetime import timedelta
import re
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.modules.authentication.repository import AuthRepository
from app.modules.authentication.models import User, UserRole
from app.modules.organization.models import Organization, OrganizationStatus
from app.modules.organization.service import OrganizationService
from app.modules.authentication.schemas import (
    LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest,
    BootstrapRequest, BootstrapResponse
)
from app.shared.security.jwt import create_access_token
from app.shared.security.password import hash_password, verify_password
from app.shared.exceptions.custom_exceptions import AuthenticationException, ValidationException, ResourceNotFoundException, ConflictException
from app.shared.logging.logger import app_logger


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = AuthRepository(session)
        self.org_service = OrganizationService(session)
        self.session = session

    async def bootstrap(self, request: BootstrapRequest) -> BootstrapResponse:
        """
        Bootstrap the system - creates the first organization and admin user.

        Uses PostgreSQL advisory lock to prevent race conditions during bootstrap.
        Returns 409 Conflict if system is already bootstrapped or bootstrap is in progress.
        Never returns an existing admin's token.
        """
        # Advisory lock key for bootstrap (fixed constant)
        BOOTSTRAP_LOCK_KEY = 987654321

        # Try to acquire advisory lock (non-blocking)
        lock_result = await self.session.execute(
            select(text("pg_try_advisory_lock(:key)")).params(key=BOOTSTRAP_LOCK_KEY)
        )
        lock_acquired = lock_result.scalar_one()

        if not lock_acquired:
            # Another bootstrap is in progress or already completed
            app_logger.warning("Bootstrap attempted but lock not acquired - another bootstrap in progress or completed")
            raise ConflictException("System bootstrap already in progress or completed")

        try:
            # Check if any admin already exists (inside the lock)
            existing_admin = await self.repo.get_first_admin()
            if existing_admin:
                app_logger.info("Bootstrap requested but system already initialized", extra={
                    "organization_id": str(existing_admin.organization_id),
                    "admin_email": existing_admin.email
                })
                raise ConflictException("System already bootstrapped")

            # Create the first organization via OrganizationService
            org = await self.org_service.create_organization(
                name=request.organization_name,
                slug=request.organization_slug
            )

            # Create root admin user
            admin_user = User(
                email=request.admin_email,
                password_hash=hash_password(request.admin_password),
                full_name=request.admin_full_name,
                role=UserRole.ADMIN,
                is_active=True,
                organization_id=org.organization_id
            )
            admin_user = await self.repo.create(admin_user)

            token = self.create_token(admin_user)
            app_logger.info(f"System bootstrapped successfully", extra={"organization_id": str(org.organization_id), "admin_email": request.admin_email})

            return BootstrapResponse(
                message="System bootstrapped successfully",
                organization_id=str(org.organization_id),
                user_id=str(admin_user.user_id),
                access_token=token,
                token_type="bearer"
            )
        finally:
            # Always release the advisory lock
            await self.session.execute(
                select(text("pg_advisory_unlock(:key)")).params(key=BOOTSTRAP_LOCK_KEY)
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
            "sub": str(user.user_id),
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
        await self.repo.update(user)
        app_logger.info(f"Password changed", extra={"user_id": user_id})

    def create_token(self, user: User) -> str:
        token_data = {
            "sub": str(user.user_id),
            "organization_id": str(user.organization_id),
            "role": user.role.value,
        }
        return create_access_token(token_data)