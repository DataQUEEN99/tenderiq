"""
AI services for document processing and content management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.modules.document.models import DocumentProcessing, DocumentContent, DocumentStatus
from app.modules.document.repository import DocumentProcessingRepository, DocumentContentRepository
from app.shared.logging.logger import app_logger
from datetime import datetime, timezone


class DocumentProcessingService:
    """Service for managing document processing state and progress.

    Uses DocumentProcessingRepository for all database operations.
    All queries are scoped by organization_id for tenant isolation.
    """

    def __init__(self, session: AsyncSession):
        self.repo = DocumentProcessingRepository(session)

    async def start_processing(self, document_id: UUID, organization_id: UUID) -> DocumentProcessing:
        """Start a new processing record for a document."""
        processing = await self.repo.get_by_document_id(document_id, organization_id)

        if not processing:
            processing = DocumentProcessing(
                document_id=document_id,
                stage="initialization",
                status="processing",
                progress=0,
                started_at=datetime.now(timezone.utc),
            )
            processing = await self.repo.create(processing)
        else:
            processing.stage = "initialization"
            processing.status = "processing"
            processing.progress = 0
            processing.started_at = datetime.now(timezone.utc)
            processing.error_message = None
            processing = await self.repo.update(processing)

        app_logger.info(f"Started document processing", extra={
            "document_id": str(document_id),
            "stage": "initialization"
        })

        return processing

    async def update_progress(self, document_id: UUID, organization_id: UUID, stage: str, progress: int) -> DocumentProcessing:
        """Update the processing progress for a document."""
        processing = await self.repo.get_by_document_id(document_id, organization_id)

        if not processing:
            processing = DocumentProcessing(
                document_id=document_id,
                stage=stage,
                status="processing",
                progress=progress,
                started_at=datetime.now(timezone.utc),
            )
            processing = await self.repo.create(processing)
        else:
            processing.stage = stage
            processing.progress = progress
            processing = await self.repo.update(processing)

        app_logger.debug(f"Processing progress update", extra={
            "document_id": str(document_id),
            "stage": stage,
            "progress": progress
        })

        return processing

    async def complete_processing(
        self,
        document_id: UUID,
        organization_id: UUID,
        chunk_count: int,
        vector_collection: str,
        text_content: str,
        page_count: int = None,
        char_count: int = None,
        extraction_method: str = None,
    ) -> DocumentProcessing:
        """Mark document processing as completed."""
        processing = await self.repo.get_by_document_id(document_id, organization_id)

        if processing:
            processing.stage = "completed"
            processing.status = "completed"
            processing.progress = 100
            processing.completed_at = datetime.now(timezone.utc)
            processing.processing_metadata = {
                "chunk_count": chunk_count,
                "vector_collection": vector_collection,
                "page_count": page_count,
                "char_count": char_count,
                "extraction_method": extraction_method,
            }
            processing = await self.repo.update(processing)

            app_logger.info(f"Completed document processing", extra={
                "document_id": str(document_id),
                "chunk_count": chunk_count,
                "vector_collection": vector_collection
            })

        return processing

    async def fail_processing(
        self,
        document_id: UUID,
        organization_id: UUID,
        error_message: str,
    ) -> DocumentProcessing:
        """Mark document processing as failed."""
        processing = await self.repo.get_by_document_id(document_id, organization_id)

        if processing:
            processing.stage = "failed"
            processing.status = "failed"
            processing.error_message = error_message
            processing.completed_at = datetime.now(timezone.utc)
            processing = await self.repo.update(processing)

            app_logger.error(f"Document processing failed", extra={
                "document_id": str(document_id),
                "error": error_message
            })

        return processing


class DocumentContentService:
    """Service for managing document content storage.

    Uses DocumentContentRepository for all database operations.
    All queries are scoped by organization_id for tenant isolation.
    """

    def __init__(self, session: AsyncSession):
        self.repo = DocumentContentRepository(session)

    async def save_content(
        self,
        document_id: UUID,
        organization_id: UUID,
        text_content: str,
        page_count: int = None,
        char_count: int = None,
        extraction_method: str = None,
    ) -> DocumentContent:
        """Save extracted document content."""
        word_count = len(text_content.split()) if text_content else 0
        character_count = char_count or len(text_content) if text_content else 0

        content = await self.repo.upsert(
            document_id=document_id,
            extracted_text=text_content,
            page_count=page_count,
            character_count=character_count,
            extraction_method=extraction_method or "unknown",
            organization_id=organization_id,
        )

        return content

    async def get_content(self, document_id: UUID, organization_id: UUID) -> DocumentContent:
        """Get document content by document ID with tenant isolation."""
        return await self.repo.get_by_document_id(document_id, organization_id)