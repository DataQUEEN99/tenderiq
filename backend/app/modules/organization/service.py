from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
import re
import uuid
from app.modules.organization.repository import OrganizationRepository
from app.modules.organization.models import Organization, OrganizationStatus
from app.modules.organization.schemas import OrganizationCreate, OrganizationUpdate, OrganizationStatusUpdate, OrganizationResponse
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, BusinessRuleViolationException
from app.shared.logging.logger import app_logger


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.repo = OrganizationRepository(session)

    async def create(self, request: OrganizationCreate) -> OrganizationResponse:
        existing = await self.repo.get_by_slug(request.slug)
        if existing:
            raise ValidationException("Organization slug already exists")

        existing = await self.repo.get_by_name(request.name)
        if existing:
            raise ValidationException("Organization name already exists")

        organization = Organization(name=request.name, slug=request.slug)
        organization = await self.repo.create(organization)
        app_logger.info(f"Organization created", extra={"organization_id": str(organization.organization_id)})
        return OrganizationResponse.model_validate(organization)

    async def get_by_id(self, org_id: UUID) -> OrganizationResponse:
        organization = await self.repo.get_by_id(org_id)
        if not organization or organization.is_deleted:
            raise ResourceNotFoundException("Organization not found")
        return OrganizationResponse.model_validate(organization)

    async def update(self, org_id: UUID, request: OrganizationUpdate) -> OrganizationResponse:
        organization = await self.repo.get_by_id(org_id)
        if not organization or organization.is_deleted:
            raise ResourceNotFoundException("Organization not found")

        if request.slug and request.slug != organization.slug:
            existing = await self.repo.get_by_slug(request.slug)
            if existing:
                raise ValidationException("Organization slug already exists")
            organization.slug = request.slug

        if request.name and request.name != organization.name:
            existing = await self.repo.get_by_name(request.name)
            if existing:
                raise ValidationException("Organization name already exists")
            organization.name = request.name

        organization = await self.repo.update(organization)
        return OrganizationResponse.model_validate(organization)

    async def update_status(self, org_id: UUID, request: OrganizationStatusUpdate) -> OrganizationResponse:
        organization = await self.repo.get_by_id(org_id)
        if not organization or organization.is_deleted:
            raise ResourceNotFoundException("Organization not found")

        organization.status = request.status
        organization = await self.repo.update(organization)
        app_logger.info(f"Organization status updated", extra={"organization_id": str(org_id), "status": request.status.value})
        return OrganizationResponse.model_validate(organization)

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[OrganizationResponse], int]:
        items, total = await self.repo.list(page, page_size)
        return [OrganizationResponse.model_validate(item) for item in items], total

    async def soft_delete(self, org_id: UUID) -> None:
        organization = await self.repo.get_by_id(org_id)
        if not organization:
            raise ResourceNotFoundException("Organization not found")
        organization.is_deleted = True
        organization.status = OrganizationStatus.DISABLED
        await self.repo.update(organization)
        app_logger.info(f"Organization soft deleted", extra={"organization_id": str(org_id)})

    async def create_organization(self, name: str, slug: str = None) -> Organization:
        """
        Create a new organization with the given name and optional slug.
        If slug is not provided, generates one from the name.
        Returns the Organization model (not the response schema).
        """
        if slug is None:
            slug = re.sub(r'[^a-zA-Z0-9]', '-', name.lower()).strip('-')

        # Check slug uniqueness
        existing = await self.repo.get_by_slug(slug)
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

        # Check name uniqueness
        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValidationException("Organization name already exists")

        organization = Organization(
            name=name,
            slug=slug,
            status=OrganizationStatus.ACTIVE,
            is_deleted=False
        )
        organization = await self.repo.create(organization)
        app_logger.info(f"Organization created", extra={"organization_id": str(organization.organization_id)})
        return organization