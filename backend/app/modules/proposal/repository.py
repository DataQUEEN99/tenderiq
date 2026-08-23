from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.proposal.models import Proposal, ProposalStatus, ProposalSection, ProposalDocument
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ProposalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, proposal_id: UUID) -> Optional[Proposal]:
        result = await self.session.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, proposal_id: UUID) -> Optional[Proposal]:
        result = await self.session.execute(
            select(Proposal)
            .options(
                selectinload(Proposal.sections),
                selectinload(Proposal.documents).selectinload(ProposalDocument.document)
            )
            .where(Proposal.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tender(self, tender_id: UUID, organization_id: UUID) -> List[Proposal]:
        result = await self.session.execute(
            select(Proposal).where(
                and_(
                    Proposal.tender_id == tender_id,
                    Proposal.organization_id == organization_id,
                    Proposal.is_deleted == False
                )
            ).order_by(Proposal.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, proposal: Proposal) -> Proposal:
        self.session.add(proposal)
        await self.session.flush()
        await self.session.refresh(proposal)
        return proposal

    async def update(self, proposal: Proposal) -> Proposal:
        await self.session.flush()
        await self.session.refresh(proposal)
        return proposal

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   status: ProposalStatus = None, tender_id: UUID = None) -> Tuple[List[Proposal], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(Proposal).where(
            and_(Proposal.organization_id == organization_id, Proposal.is_deleted == False)
        )

        if status:
            query = query.where(Proposal.status == status)
        if tender_id:
            query = query.where(Proposal.tender_id == tender_id)

        query = query.order_by(Proposal.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(Proposal.id)).where(
            and_(Proposal.organization_id == organization_id, Proposal.is_deleted == False)
        )
        if status:
            count_query = count_query.where(Proposal.status == status)
        if tender_id:
            count_query = count_query.where(Proposal.tender_id == tender_id)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

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
                and_(ProposalSection.id == section_id, ProposalSection.proposal_id == proposal_id, ProposalSection.is_deleted == False)
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
                and_(ProposalSection.id == section_id, ProposalSection.proposal_id == proposal_id)
            )
        )
        section = result.scalar_one_or_none()
        if section:
            await self.session.delete(section)
            await self.session.flush()
            return True
        return False

    async def attach_documents(self, proposal_id: UUID, document_ids: List[UUID]) -> List[ProposalDocument]:
        links = []
        for doc_id in document_ids:
            link = ProposalDocument(proposal_id=proposal_id, document_id=doc_id)
            self.session.add(link)
            links.append(link)
        await self.session.flush()
        return links

    async def detach_document(self, proposal_id: UUID, document_id: UUID) -> bool:
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

    async def soft_delete(self, proposal_id: UUID) -> bool:
        proposal = await self.get_by_id(proposal_id)
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