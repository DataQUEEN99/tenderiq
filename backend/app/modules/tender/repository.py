from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.tender.models import Tender, TenderStatus, TenderDocument
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class TenderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, tender_id: UUID) -> Optional[Tender]:
        result = await self.session.execute(
            select(Tender).where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_docs(self, tender_id: UUID) -> Optional[Tender]:
        result = await self.session.execute(
            select(Tender)
            .options(selectinload(Tender.documents).selectinload(TenderDocument.document))
            .where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()

    async def get_by_reference(self, organization_id: UUID, reference_number: str) -> Optional[Tender]:
        result = await self.session.execute(
            select(Tender).where(
                and_(
                    Tender.organization_id == organization_id,
                    Tender.reference_number == reference_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, tender: Tender) -> Tender:
        self.session.add(tender)
        await self.session.flush()
        await self.session.refresh(tender)
        return tender

    async def update(self, tender: Tender) -> Tender:
        await self.session.flush()
        await self.session.refresh(tender)
        return tender

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   status: TenderStatus = None, search: str = None) -> Tuple[List[Tender], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(Tender).where(
            and_(Tender.organization_id == organization_id, Tender.is_deleted == False)
        )

        if status:
            query = query.where(Tender.status == status)

        if search:
            query = query.where(
                or_(
                    Tender.title.ilike(f"%{search}%"),
                    Tender.reference_number.ilike(f"%{search}%"),
                    Tender.issuing_authority.ilike(f"%{search}%")
                )
            )

        query = query.order_by(Tender.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(Tender.id)).where(
            and_(Tender.organization_id == organization_id, Tender.is_deleted == False)
        )
        if status:
            count_query = count_query.where(Tender.status == status)
        if search:
            count_query = count_query.where(
                or_(
                    Tender.title.ilike(f"%{search}%"),
                    Tender.reference_number.ilike(f"%{search}%"),
                    Tender.issuing_authority.ilike(f"%{search}%")
                )
            )

        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def attach_documents(self, tender_id: UUID, document_ids: List[UUID]) -> List[TenderDocument]:
        links = []
        for doc_id in document_ids:
            link = TenderDocument(tender_id=tender_id, document_id=doc_id)
            self.session.add(link)
            links.append(link)
        await self.session.flush()
        return links

    async def detach_document(self, tender_id: UUID, document_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenderDocument).where(
                and_(TenderDocument.tender_id == tender_id, TenderDocument.document_id == document_id)
            )
        )
        link = result.scalar_one_or_none()
        if link:
            await self.session.delete(link)
            await self.session.flush()
            return True
        return False

    async def get_attached_documents(self, tender_id: UUID) -> List[TenderDocument]:
        result = await self.session.execute(
            select(TenderDocument)
            .options(selectinload(TenderDocument.document))
            .where(TenderDocument.tender_id == tender_id)
        )
        return result.scalars().all()

    async def soft_delete(self, tender_id: UUID) -> bool:
        tender = await self.get_by_id(tender_id)
        if not tender:
            return False
        tender.is_deleted = True
        tender.status = TenderStatus.ARCHIVED
        await self.session.flush()
        return True