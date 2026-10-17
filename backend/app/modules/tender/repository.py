from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.tender.models import Tender, TenderStatus, TenderDocument
from app.modules.document.models import Document
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.database.tenant_repository import TenantRepository


class TenderRepository(TenantRepository[Tender]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Tender, primary_key_attr='tender_id')

    async def get_by_id(self, tender_id: UUID, organization_id: UUID) -> Optional[Tender]:
        return await super().get_by_id(tender_id, organization_id)

    async def get_by_id_with_docs(self, tender_id: UUID, organization_id: UUID) -> Optional[Tender]:
        query = select(Tender).options(
            selectinload(Tender.documents).selectinload(TenderDocument.document)
        ).where(Tender.tender_id == tender_id)
        tenant_filter = self._tenant_filter(organization_id)
        if tenant_filter is not None:
            query = query.where(tenant_filter)
        result = await self.session.execute(query)
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

    # create and update are inherited from TenantRepository

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   status: TenderStatus = None, search: str = None) -> Tuple[List[Tender], int]:
        filters = {}
        if status:
            filters['status'] = status
        # Search is a special case - we'll keep custom implementation
        if search:
            return await self._search(organization_id, page, page_size, search, filters)
        return await super().list(organization_id, page, page_size, **filters)

    async def _search(self, organization_id: UUID, page: int, page_size: int,
                      search: str, filters: dict) -> Tuple[List[Tender], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(Tender)
        tenant_filter = self._tenant_filter(organization_id)
        if tenant_filter is not None:
            query = query.where(tenant_filter)
        if hasattr(self.model, 'is_deleted'):
            query = query.where(self.model.is_deleted == False)

        if filters.get('status'):
            query = query.where(Tender.status == filters['status'])

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

        count_query = select(func.count(Tender.tender_id))
        if tenant_filter is not None:
            count_query = count_query.where(tenant_filter)
        if hasattr(self.model, 'is_deleted'):
            count_query = count_query.where(self.model.is_deleted == False)
        if filters.get('status'):
            count_query = count_query.where(Tender.status == filters['status'])
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

    async def attach_documents(self, tender_id: UUID, organization_id: UUID, document_ids: List[UUID]) -> List[TenderDocument]:
        # Verify tender belongs to organization
        tender = await self.get_by_id(tender_id, organization_id)
        if not tender:
            raise ValueError("Tender not found")

        links = []
        for doc_id in document_ids:
            document = await self.session.execute(
                select(Document).where(
                    and_(
                        Document.document_id == doc_id,
                        Document.organization_id == organization_id,
                        Document.status != DocumentStatus.DELETED,
                    )
                )
            )
            if not document.scalar_one_or_none():
                raise ValueError(f"Document {doc_id} not found or not accessible")
            link = TenderDocument(tender_id=tender_id, document_id=doc_id)
            self.session.add(link)
            links.append(link)
        await self.session.flush()
        return links

    async def detach_document(self, tender_id: UUID, organization_id: UUID, document_id: UUID) -> bool:
        # Verify tender belongs to organization
        tender = await self.get_by_id(tender_id, organization_id)
        if not tender:
            return False

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

    async def get_attached_documents(self, tender_id: UUID, organization_id: UUID) -> List[TenderDocument]:
        # Verify tender belongs to organization
        tender = await self.get_by_id(tender_id, organization_id)
        if not tender:
            return []

        result = await self.session.execute(
            select(TenderDocument)
            .options(selectinload(TenderDocument.document))
            .where(TenderDocument.tender_id == tender_id)
        )
        return result.scalars().all()

    async def soft_delete(self, tender_id: UUID, organization_id: UUID) -> bool:
        tender = await self.get_by_id(tender_id, organization_id)
        if not tender:
            return False
        tender.status = TenderStatus.ARCHIVED
        await self.session.flush()
        return True