"""
AI services for document processing and content management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select
from app.modules.document.models import DocumentProcessing, DocumentContent, DocumentStatus
from app.shared.logging.logger import app_logger
from datetime import datetime, timezone


class DocumentProcessingService:
    """Service for managing document processing state and progress."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_processing(self, document_id: UUID, organization_id: UUID) -> DocumentProcessing:
        """Start a new processing record for a document."""
        # Check if processing record already exists
        result = await self.session.execute(
            select(DocumentProcessing).where(DocumentProcessing.document_id == document_id)
        )
        processing = result.scalar_one_or_none()

        if not processing:
            processing = DocumentProcessing(
                document_id=document_id,
                stage="initialization",
                status="processing",
                progress=0,
                started_at=datetime.now(timezone.utc),
            )
            self.session.add(processing)
        else:
            processing.stage = "initialization"
            processing.status = "processing"
            processing.progress = 0
            processing.started_at = datetime.now(timezone.utc)
            processing.error_message = None

        await self.session.flush()
        await self.session.refresh(processing)

        app_logger.info(f"Started document processing", extra={
            "document_id": str(document_id),
            "stage": "initialization"
        })

        return processing

    async def update_progress(self, document_id: UUID, stage: str, progress: int) -> DocumentProcessing:
        """Update the processing progress for a document."""
        result = await self.session.execute(
            select(DocumentProcessing).where(DocumentProcessing.document_id == document_id)
        )
        processing = result.scalar_one_or_none()

        if not processing:
            processing = DocumentProcessing(
                document_id=document_id,
                stage=stage,
                status="processing",
                progress=progress,
                started_at=datetime.now(timezone.utc),
            )
            self.session.add(processing)
        else:
            processing.stage = stage
            processing.progress = progress

        await self.session.flush()
        await self.session.refresh(processing)

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
        result = await self.session.execute(
            select(DocumentProcessing).where(DocumentProcessing.document_id == document_id)
        )
        processing = result.scalar_one_or_none()

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

            await self.session.flush()
            await self.session.refresh(processing)

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
        result = await self.session.execute(
            select(DocumentProcessing).where(DocumentProcessing.document_id == document_id)
        )
        processing = result.scalar_one_or_none()

        if processing:
            processing.stage = "failed"
            processing.status = "failed"
            processing.error_message = error_message
            processing.completed_at = datetime.now(timezone.utc)

            await self.session.flush()
            await self.session.refresh(processing)

            app_logger.error(f"Document processing failed", extra={
                "document_id": str(document_id),
                "error": error_message
            })

        return processing


class DocumentContentService:
    """Service for managing document content storage."""

    def __init__(self, session: AsyncSession):
        self.session = session

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
        # Check if content record already exists
        result = await self.session.execute(
            select(DocumentContent).where(DocumentContent.document_id == document_id)
        )
        content = result.scalar_one_or_none()

        if not content:
            content = DocumentContent(
                document_id=document_id,
                extracted_text=text_content,
                extraction_method=extraction_method or "unknown",
                extraction_status="completed",
                page_count=page_count,
                word_count=len(text_content.split()) if text_content else 0,
                character_count=char_count or len(text_content) if text_content else 0,
                extracted_at=datetime.now(timezone.utc),
            )
            self.session.add(content)
        else:
            content.extracted_text = text_content
            content.extraction_method = extraction_method or "unknown"
            content.extraction_status = "completed"
            content.page_count = page_count
            content.word_count = len(text_content.split()) if text_content else 0
            content.character_count = char_count or len(text_content) if text_content else 0
            content.extracted_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(content)

        return content

    async def get_content(self, document_id: UUID) -> DocumentContent:
        """Get document content by document ID."""
        result = await self.session.execute(
            select(DocumentContent).where(DocumentContent.document_id == document_id)
        )
        return result.scalar_one_or_none()