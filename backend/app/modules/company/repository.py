from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.modules.company.models import CompanyProfile, CompanyDocument
from app.shared.database.base import BaseModel


class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_organization(self, organization_id: UUID) -> Optional[CompanyProfile]:
        result = await self.session.execute(
            select(CompanyProfile).where(CompanyProfile.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID) -> Optional[CompanyProfile]:
        result = await self.session.execute(
            select(CompanyProfile).where(CompanyProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: CompanyProfile) -> CompanyProfile:
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update(self, profile: CompanyProfile) -> CompanyProfile:
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def attach_document(self, profile_id: UUID, document_id: UUID, document_type: Optional[str] = None) -> CompanyDocument:
        link = CompanyDocument(
            company_profile_id=profile_id,
            document_id=document_id,
            document_type=document_type
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def get_documents(self, profile_id: UUID) -> List[CompanyDocument]:
        result = await self.session.execute(
            select(CompanyDocument).where(CompanyDocument.company_profile_id == profile_id)
        )
        return list(result.scalars().all())

    async def detach_document(self, profile_id: UUID, document_id: UUID) -> bool:
        result = await self.session.execute(
            select(CompanyDocument).where(
                and_(
                    CompanyDocument.company_profile_id == profile_id,
                    CompanyDocument.document_id == document_id
                )
            )
        )
        link = result.scalar_one_or_none()
        if link:
            await self.session.delete(link)
            await self.session.flush()
            return True
        return False