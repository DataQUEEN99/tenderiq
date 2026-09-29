from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.modules.company.models import CompanyProfile, CompanyDocument
from app.modules.document.models import Document
from app.shared.database.tenant_repository import TenantRepository
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class CompanyRepository(TenantRepository[CompanyProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CompanyProfile, primary_key_attr='company_profile_id')

    async def get_by_organization(self, organization_id: UUID) -> Optional[CompanyProfile]:
        result = await self.session.execute(
            select(CompanyProfile).where(
                and_(
                    CompanyProfile.organization_id == organization_id,
                    CompanyProfile.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID, organization_id: UUID) -> Optional[CompanyProfile]:
        return await super().get_by_id(profile_id, organization_id)

    async def create(self, profile: CompanyProfile) -> CompanyProfile:
        return await super().create(profile)

    async def update(self, profile: CompanyProfile) -> CompanyProfile:
        return await super().update(profile)

    async def soft_delete(self, profile_id: UUID, organization_id: UUID) -> bool:
        return await super().soft_delete(profile_id, organization_id)

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> tuple[List[CompanyProfile], int]:
        return await super().list(organization_id, page, page_size)


class CompanyDocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def attach_document(self, profile_id: UUID, organization_id: UUID, document_id: UUID,
                              created_by: UUID, document_type: str = "primary") -> CompanyDocument:
        # Verify company profile belongs to organization
        profile = await self.session.execute(
            select(CompanyProfile).where(
                and_(
                    CompanyProfile.company_profile_id == profile_id,
                    CompanyProfile.organization_id == organization_id,
                    CompanyProfile.is_deleted == False
                )
            )
        )
        if not profile.scalar_one_or_none():
            raise ValueError("Company profile not found or not accessible")

        document = await self.session.execute(
            select(Document).where(
                and_(
                    Document.document_id == document_id,
                    Document.organization_id == organization_id,
                    Document.is_deleted == False,
                )
            )
        )
        if not document.scalar_one_or_none():
            raise ValueError(f"Document {document_id} not found or not accessible")

        link = CompanyDocument(
            company_profile_id=profile_id,
            document_id=document_id,
            relationship_type=document_type,
            created_by=created_by,
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def get_documents(self, profile_id: UUID, organization_id: UUID) -> List[CompanyDocument]:
        # Verify company profile belongs to organization
        profile = await self.session.execute(
            select(CompanyProfile).where(
                and_(
                    CompanyProfile.company_profile_id == profile_id,
                    CompanyProfile.organization_id == organization_id,
                    CompanyProfile.is_deleted == False
                )
            )
        )
        if not profile.scalar_one_or_none():
            return []

        result = await self.session.execute(
            select(CompanyDocument).where(CompanyDocument.company_profile_id == profile_id)
        )
        return list(result.scalars().all())

    async def detach_document(self, profile_id: UUID, organization_id: UUID, document_id: UUID) -> bool:
        # Verify company profile belongs to organization
        profile = await self.session.execute(
            select(CompanyProfile).where(
                and_(
                    CompanyProfile.company_profile_id == profile_id,
                    CompanyProfile.organization_id == organization_id,
                    CompanyProfile.is_deleted == False
                )
            )
        )
        if not profile.scalar_one_or_none():
            return False

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