from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.document.models import Document, DocumentStatus, DocumentType
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        result = await self.session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, organization_id: UUID, file_hash: str) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(
                and_(
                    Document.organization_id == organization_id,
                    Document.file_hash == file_hash,
                    Document.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def update_status(self, doc_id: UUID, status: DocumentStatus, error_message: str = None,
                            chunk_count: int = None, vector_collection: str = None) -> Optional[Document]:
        document = await self.get_by_id(doc_id)
        if not document:
            return None

        document.status = status
        if error_message:
            document.error_message = error_message
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if vector_collection:
            document.vector_collection = vector_collection

        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   document_type: DocumentType = None, status: DocumentStatus = None) -> Tuple[List[Document], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(Document).where(
            and_(Document.organization_id == organization_id, Document.is_deleted == False)
        )

        if document_type:
            query = query.where(Document.document_type == document_type)
        if status:
            query = query.where(Document.status == status)

        query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(Document.id)).where(
            and_(Document.organization_id == organization_id, Document.is_deleted == False)
        )
        if document_type:
            count_query = count_query.where(Document.document_type == document_type)
        if status:
            count_query = count_query.where(Document.status == status)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def soft_delete(self, doc_id: UUID) -> bool:
        document = await self.get_by_id(doc_id)
        if not document:
            return False
        document.is_deleted = True
        document.status = DocumentStatus.DELETED
        await self.session.flush()
        return True