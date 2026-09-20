"""
Celery tasks for document processing pipeline.
"""
import logging
from celery import shared_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select
from app.config import get_settings
from app.shared.database.session import Base
from app.shared.database.transaction import UnitOfWork

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create async engine for background tasks
engine = create_async_engine(settings.database_url, echo=settings.database_echo)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 3},
    name="app.tasks.document_tasks.process_document"
)
def process_document(self, document_id: str, organization_id: str):
    """
    Process a document through the complete pipeline:
    text extraction -> chunking -> embedding -> vector indexing -> persistence

    This task runs in a Celery worker with automatic retry on failure.
    Uses explicit transaction management: BEGIN -> processing -> COMMIT/ROLLBACK
    """
    import asyncio

    async def _process():
        async with async_session_maker() as session:
            uow = UnitOfWork(session)
            async with uow:
                # Import here to avoid circular imports
                from app.modules.document.processing_service import DocumentProcessingPipeline

                pipeline = DocumentProcessingPipeline(session)
                result = await pipeline.process_document(
                    document_id=UUID(document_id),
                    organization_id=UUID(organization_id)
                )
            # Transaction committed automatically on success
            return result

    try:
        result = asyncio.run(_process())
        logger.info(f"Document processing completed", extra={
            "document_id": document_id,
            "success": result.get("success", False)
        })
        return result
    except Exception as e:
        logger.error(f"Document processing failed", extra={
            "document_id": document_id,
            "error": str(e),
            "retry_count": self.request.retries
        })
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 3},
    name="app.tasks.document_tasks.reprocess_document"
)
def reprocess_document(self, document_id: str, organization_id: str):
    """
    Reprocess a document through the complete pipeline.
    Uses explicit transaction management: BEGIN -> processing -> COMMIT/ROLLBACK
    """
    import asyncio

    async def _reprocess():
        async with async_session_maker() as session:
            uow = UnitOfWork(session)
            async with uow:
                from app.modules.document.processing_service import DocumentProcessingPipeline

                pipeline = DocumentProcessingPipeline(session)
                result = await pipeline.process_document(
                    document_id=UUID(document_id),
                    organization_id=UUID(organization_id)
                )
            # Transaction committed automatically on success
            return result

    try:
        result = asyncio.run(_reprocess())
        logger.info(f"Document reprocessing completed", extra={
            "document_id": document_id,
            "success": result.get("success", False)
        })
        return result
    except Exception as e:
        logger.error(f"Document reprocessing failed", extra={
            "document_id": document_id,
            "error": str(e),
            "retry_count": self.request.retries
        })
        raise


@shared_task(name="app.tasks.document_tasks.cleanup_failed_documents")
def cleanup_failed_documents():
    """
    Periodic task to clean up documents stuck in PROCESSING state.
    Uses explicit transaction management: BEGIN -> processing -> COMMIT/ROLLBACK
    """
    import asyncio

    async def _cleanup():
        async with async_session_maker() as session:
            uow = UnitOfWork(session)
            async with uow:
                from app.modules.document.repository import DocumentRepository
                from app.modules.document.models import Document, DocumentStatus
                from datetime import datetime, timedelta, timezone

                repo = DocumentRepository(session)

                # Find documents stuck in PROCESSING for more than 1 hour
                cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
                result = await session.execute(
                    select(Document).where(
                        Document.status == DocumentStatus.PROCESSING,
                        Document.updated_at < cutoff
                    )
                )
                stuck_docs = result.scalars().all()

                for doc in stuck_docs:
                    await repo.update_status(
                        document_id=doc.document_id,
                        organization_id=doc.organization_id,
                        status=DocumentStatus.FAILED,
                        error_message="Processing timeout - marked as failed by cleanup task"
                    )
                    logger.warning(f"Marked stuck document as failed", extra={
                        "document_id": str(doc.document_id)
                    })

            # Transaction committed automatically on success
            return len(stuck_docs)

    try:
        count = asyncio.run(_cleanup())
        logger.info(f"Cleanup completed", extra={"stuck_documents_fixed": count})
        return {"cleaned": count}
    except Exception as e:
        logger.error(f"Cleanup failed", extra={"error": str(e)})
        raise