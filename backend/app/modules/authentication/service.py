from datetime import timedelta
import re
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.modules.authentication.repository import AuthRepository
from app.modules.authentication.models import User, UserRole
from app.modules.organization.models import Organization, OrganizationStatus
from app.modules.organization.service import OrganizationService
from app.modules.organization.schemas import OrganizationResponse
from app.modules.authentication.schemas import (
    LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest,
    BootstrapRequest, BootstrapResponse, RegisterOrgRequest, GoogleAuthRequest
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

    async def register_organization(self, request: RegisterOrgRequest) -> LoginResponse:
        """Register a new organization with an initial admin user."""
        org_name = (request.org_name or request.organization_name or "").strip()
        email = (request.email or request.admin_email or "").strip().lower()
        password = request.password or request.admin_password or ""
        full_name = (request.full_name or request.admin_full_name or "").strip()

        if not org_name:
            raise ValidationException("Organization name is required")
        if not email:
            raise ValidationException("Email is required")
        if not password or len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")
        if not full_name:
            full_name = email.split("@")[0].capitalize()

        existing_user = await self.repo.get_by_email(email)
        if existing_user:
            raise ConflictException("An account with this email already exists")

        # Create organization
        org = await self.org_service.create_organization(
            name=org_name,
            slug=None
        )

        # Create admin user
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=org.organization_id
        )
        admin_user = await self.repo.create(admin_user)
        admin_user.organization = org

        token = self.create_token(admin_user)
        app_logger.info("New organization registered", extra={
            "organization_id": str(org.organization_id),
            "admin_email": email
        })

        return LoginResponse(
            access_token=token,
            refresh_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(admin_user),
            organization=OrganizationResponse.model_validate(org),
        )

    async def login_google(self, request: GoogleAuthRequest) -> LoginResponse:
        """Authenticate or register user via Google."""
        email = (request.email or "").strip().lower()
        full_name = (request.full_name or "").strip()

        # If id_token passed, attempt to parse payload if possible
        if request.id_token and not email:
            try:
                import base64
                import json
                parts = request.id_token.split(".")
                if len(parts) >= 2:
                    padding = 4 - len(parts[1]) % 4
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * padding))
                    email = (payload.get("email") or "").strip().lower()
                    full_name = payload.get("name") or full_name
            except Exception as e:
                app_logger.warning(f"Could not parse Google id_token: {e}")

        if not email:
            raise ValidationException("Google authentication requires a valid email")

        if not full_name:
            full_name = email.split("@")[0].replace(".", " ").capitalize()

        user = await self.repo.get_by_email(email)
        if not user:
            # Auto-register organization and user
            org_name = f"{full_name}'s Organization"
            org = await self.org_service.create_organization(
                name=org_name,
                slug=None
            )

            user = User(
                email=email,
                password_hash=hash_password(uuid.uuid4().hex),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
                organization_id=org.organization_id
            )
            user = await self.repo.create(user)
            user.organization = org
            app_logger.info("New user auto-created via Google", extra={
                "organization_id": str(org.organization_id),
                "email": email
            })
        else:
            if not user.is_active:
                raise AuthenticationException("Account is deactivated")
            if not user.organization:
                user.organization = await self.org_service.repo.get_by_id(user.organization_id)

        token = self.create_token(user)
        return LoginResponse(
            access_token=token,
            refresh_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(user.organization) if user.organization else None,
        )

    async def bootstrap(self, request: BootstrapRequest) -> BootstrapResponse:
        """
        Bootstrap the system - creates the first organization and admin user.
        If an admin already exists, creates a new organization smoothly.
        """
        # Check if any admin already exists
        existing_admin = await self.repo.get_first_admin()
        if existing_admin:
            res = await self.register_organization(RegisterOrgRequest(
                organization_name=request.organization_name,
                admin_email=request.admin_email,
                admin_password=request.admin_password,
                admin_full_name=request.admin_full_name,
            ))
            return BootstrapResponse(
                message="Organization registered successfully",
                organization_id=str(res.organization.organization_id if res.organization else res.user.organization_id),
                user_id=str(res.user.user_id),
                access_token=res.access_token,
                token_type="bearer"
            )

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

        org_resp = None
        if user.organization:
            org_resp = OrganizationResponse.model_validate(user.organization)

        return LoginResponse(
            access_token=access_token,
            refresh_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            organization=org_resp,
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