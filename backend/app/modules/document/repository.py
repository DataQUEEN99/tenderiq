from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.document.models import Document, DocumentStatus, DocumentType, DocumentContent, DocumentProcessing
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.database.tenant_repository import TenantRepository


class DocumentRepository(TenantRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document, primary_key_attr='document_id')

    # Override get_by_id to require organization_id
    async def get_by_id(self, doc_id: UUID, organization_id: UUID) -> Optional[Document]:
        return await super().get_by_id(doc_id, organization_id)

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

    async def get_sections(self, proposal_id: UUID) -> List:
        # Placeholder - would need ProposalSection model imported
        return []

    async def update_status(self, doc_id: UUID, organization_id: UUID, status: DocumentStatus,
                            error_message: str = None, chunk_count: int = None,
                            vector_collection: str = None) -> Optional[Document]:
        document = await self.get_by_id(doc_id, organization_id)
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

    # Override list to use the base class implementation with filters
    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   document_type: DocumentType = None, status: DocumentStatus = None) -> Tuple[List[Document], int]:
        filters = {}
        if document_type:
            filters['document_type'] = document_type
        if status:
            filters['status'] = status
        return await super().list(organization_id, page, page_size, **filters)


class DocumentContentRepository(TenantRepository[DocumentContent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentContent, primary_key_attr='document_content_id')

    async def get_by_document_id(self, document_id: UUID, organization_id: UUID = None) -> Optional[DocumentContent]:
        """Get document content by document_id, optionally scoped by organization_id for tenant isolation."""
        from app.modules.document.models import Document
        query = select(DocumentContent).where(DocumentContent.document_id == document_id)

        if organization_id is not None:
            # Join with Document to enforce tenant isolation
            query = query.join(Document).where(Document.organization_id == organization_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, content: DocumentContent) -> DocumentContent:
        return await super().create(content)

    async def update(self, content: DocumentContent) -> DocumentContent:
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def upsert(self, document_id: UUID, extracted_text: str, page_count: int = None,
                     character_count: int = None, extraction_method: str = None, organization_id: UUID = None):
        existing = await self.get_by_document_id(document_id, organization_id)
        if existing:
            existing.extracted_text = extracted_text
            existing.extraction_status = "completed"
            if page_count is not None:
                existing.page_count = page_count
            if character_count is not None:
                existing.character_count = character_count
            if extraction_method:
                existing.extraction_method = extraction_method
            return await self.update(existing)

        content = DocumentContent(
            document_id=document_id,
            extracted_text=extracted_text,
            extraction_method=extraction_method or "native",
            extraction_status="completed",
            page_count=page_count,
            character_count=character_count,
        )
        return await self.create(content)


class DocumentProcessingRepository(TenantRepository[DocumentProcessing]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentProcessing, primary_key_attr='document_processing_id')

    async def get_by_document_id(self, document_id: UUID, organization_id: UUID = None) -> Optional[DocumentProcessing]:
        """Get document processing by document_id, optionally scoped by organization_id for tenant isolation."""
        from app.modules.document.models import Document
        query = select(DocumentProcessing).where(DocumentProcessing.document_id == document_id)

        if organization_id is not None:
            # Join with Document to enforce tenant isolation
            query = query.join(Document).where(Document.organization_id == organization_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, processing: DocumentProcessing) -> DocumentProcessing:
        return await super().create(processing)

    async def update(self, processing: DocumentProcessing) -> DocumentProcessing:
        await self.session.flush()
        await self.session.refresh(processing)
        return processing

    async def upsert(self, document_id: UUID, status: str, error_message: str = None,
                     started_at=None, completed_at=None, metadata: dict = None, organization_id: UUID = None):
        existing = await self.get_by_document_id(document_id, organization_id)
        if existing:
            existing.status = status
            if error_message:
                existing.error_message = error_message
            if started_at:
                existing.started_at = started_at
            if completed_at:
                existing.completed_at = completed_at
            if metadata:
                existing.processing_metadata = metadata
            # Update stage based on status
            if status == "processing":
                existing.stage = "extraction"
            elif status == "processed":
                existing.stage = "completed"
            elif status == "failed":
                existing.stage = "failed"
            return await self.update(existing)

        # Determine stage from status
        if status == "processing":
            stage = "extraction"
        elif status == "processed":
            stage = "completed"
        elif status == "failed":
            stage = "failed"
        else:
            stage = "pending"

        processing = DocumentProcessing(
            document_id=document_id,
            stage=stage,
            status=status,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
            processing_metadata=metadata or {},
        )
        return await self.create(processing)