from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.proposal.models import Proposal, ProposalStatus, ProposalSection, ProposalDocument
from app.modules.tender.models import Tender
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.database.tenant_repository import TenantRepository


class ProposalRepository(TenantRepository[Proposal]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Proposal, primary_key_attr='proposal_id')

    async def get_by_id(self, proposal_id: UUID, organization_id: UUID) -> Optional[Proposal]:
        return await super().get_by_id(proposal_id, organization_id)

    async def get_by_id_with_details(self, proposal_id: UUID, organization_id: UUID) -> Optional[Proposal]:
        query = select(Proposal).options(
            selectinload(Proposal.sections),
            selectinload(Proposal.documents).selectinload(ProposalDocument.document)
        ).where(Proposal.proposal_id == proposal_id)
        tenant_filter = self._tenant_filter(organization_id)
        if tenant_filter is not None:
            query = query.where(tenant_filter)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_tender(self, tender_id: UUID, organization_id: UUID) -> List[Proposal]:
        return await self.list(organization_id, page_size=MAX_PAGE_SIZE, tender_id=tender_id)

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   status: ProposalStatus = None, tender_id: UUID = None) -> Tuple[List[Proposal], int]:
        filters = {}
        if status:
            filters['status'] = status
        if tender_id:
            filters['tender_id'] = tender_id
        return await super().list(organization_id, page, page_size, **filters)

    async def add_section(self, section: ProposalSection) -> ProposalSection:
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def get_sections(self, proposal_id: UUID) -> List[ProposalSection]:
        result = await self.session.execute(
            select(ProposalSection).where(
                and_(ProposalSection.proposal_id == proposal_id, ProposalSection.is_deleted == False)
            ).order_by(ProposalSection.order)
        )
        return result.scalars().all()

    async def get_proposal_sections(self, proposal_id: UUID) -> List[ProposalSection]:
        return await self.get_sections(proposal_id)

    async def get_section_by_id(self, section_id: UUID, proposal_id: UUID) -> Optional[ProposalSection]:
        result = await self.session.execute(
            select(ProposalSection).where(
                and_(ProposalSection.proposal_section_id == section_id, ProposalSection.proposal_id == proposal_id, ProposalSection.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def get_section_by_type(self, proposal_id: UUID, section_type: str) -> Optional[ProposalSection]:
        result = await self.session.execute(
            select(ProposalSection).where(
                and_(ProposalSection.proposal_id == proposal_id, ProposalSection.section_type == section_type, ProposalSection.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def update_section(self, section: ProposalSection) -> ProposalSection:
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def delete_section(self, section_id: UUID, proposal_id: UUID) -> bool:
        result = await self.session.execute(
            select(ProposalSection).where(
                and_(ProposalSection.proposal_section_id == section_id, ProposalSection.proposal_id == proposal_id)
            )
        )
        section = result.scalar_one_or_none()
        if section:
            await self.session.delete(section)
            await self.session.flush()
            return True
        return False

    async def get_section_by_id(self, section_id: UUID, proposal_id: UUID) -> Optional[ProposalSection]:
        result = await self.session.execute(
            select(ProposalSection).where(
                and_(
                    ProposalSection.proposal_section_id == section_id,
                    ProposalSection.proposal_id == proposal_id,
                    ProposalSection.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def attach_documents(self, proposal_id: UUID, organization_id: UUID, document_ids: List[UUID]) -> List[ProposalDocument]:
        # Verify proposal belongs to organization
        proposal = await self.get_by_id(proposal_id, organization_id)
        if not proposal:
            raise ValueError("Proposal not found")

        links = []
        for doc_id in document_ids:
            link = ProposalDocument(proposal_id=proposal_id, document_id=doc_id)
            self.session.add(link)
            links.append(link)
        await self.session.flush()
        return links

    async def detach_document(self, proposal_id: UUID, organization_id: UUID, document_id: UUID) -> bool:
        # Verify proposal belongs to organization
        proposal = await self.get_by_id(proposal_id, organization_id)
        if not proposal:
            return False

        result = await self.session.execute(
            select(ProposalDocument).where(
                and_(ProposalDocument.proposal_id == proposal_id, ProposalDocument.document_id == document_id)
            )
        )
        link = result.scalar_one_or_none()
        if link:
            await self.session.delete(link)
            await self.session.flush()
            return True
        return False

    async def soft_delete(self, proposal_id: UUID, organization_id: UUID) -> bool:
        proposal = await self.get_by_id(proposal_id, organization_id)
        if not proposal:
            return False
        proposal.is_deleted = True
        proposal.status = ProposalStatus.ARCHIVED
        await self.session.flush()
        return True

    async def create_version(self, proposal: Proposal) -> Proposal:
        self.session.add(proposal)
        await self.session.flush()
        await self.session.refresh(proposal)
        return proposal

    async def get_tender_by_id(self, tender_id: UUID, organization_id: UUID) -> Optional[Tender]:
        result = await self.session.execute(
            select(Tender).where(
                and_(
                    Tender.tender_id == tender_id,
                    Tender.organization_id == organization_id,
                    Tender.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_section_by_type(self, proposal_id: UUID, organization_id: UUID, section_type: str) -> Optional[ProposalSection]:
        # Verify proposal belongs to organization
        proposal = await self.get_by_id(proposal_id, organization_id)
        if not proposal:
            return None

        result = await self.session.execute(
            select(ProposalSection).where(
                and_(
                    ProposalSection.proposal_id == proposal_id,
                    ProposalSection.section_type == section_type,
                    ProposalSection.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def add_sections_bulk(self, sections: List[ProposalSection]) -> List[ProposalSection]:
        for section in sections:
            self.session.add(section)
        await self.session.flush()
        for section in sections:
            await self.session.refresh(section)
        return sections

    async def upsert_sections(self, proposal_id: UUID, organization_id: UUID, sections_data: List[dict]) -> List[ProposalSection]:
        # Verify proposal belongs to organization
        proposal = await self.get_by_id(proposal_id, organization_id)
        if not proposal:
            raise ValueError("Proposal not found")

        created_sections = []
        for sec_data in sections_data:
            existing = await self.get_section_by_type(proposal_id, organization_id, sec_data.get("section_type"))
            if existing:
                existing.content = sec_data.get("content")
                existing.is_generated = True
                existing.generation_prompt = sec_data.get("generation_prompt", f"AI generated for {sec_data.get('title')}")
                await self.session.flush()
                await self.session.refresh(existing)
                created_sections.append(existing)
            else:
                section = ProposalSection(
                    title=sec_data.get("title"),
                    content=sec_data.get("content"),
                    section_type=sec_data.get("section_type"),
                    is_generated=True,
                    generation_prompt=sec_data.get("generation_prompt", f"AI generated for {sec_data.get('title')}"),
                    proposal_id=proposal_id,
                )
                self.session.add(section)
                await self.session.flush()
                await self.session.refresh(section)
                created_sections.append(section)
        return created_sections