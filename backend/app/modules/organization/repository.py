from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.modules.organization.models import Organization, OrganizationStatus
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        result = await self.session.execute(select(Organization).where(Organization.organization_id == org_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Organization]:
        result = await self.session.execute(select(Organization).where(Organization.name == name))
        return result.scalar_one_or_none()

    async def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        await self.session.refresh(organization)
        return organization

    async def update(self, organization: Organization) -> Organization:
        """Update organization entity - flush and refresh"""
        await self.session.flush()
        await self.session.refresh(organization)
        return organization

    async def list(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> tuple[List[Organization], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        result = await self.session.execute(
            select(Organization).where(Organization.is_deleted == False).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        count_result = await self.session.execute(
            select(func.count(Organization.organization_id)).where(Organization.is_deleted == False)
        )
        total = count_result.scalar_one()

        return list(items), total