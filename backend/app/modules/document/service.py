import os
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.modules.document.repository import DocumentRepository
from app.modules.document.models import Document, DocumentStatus, DocumentType
from app.modules.document.schemas import (
    DocumentUploadRequest, DocumentResponse, DocumentSearchRequest,
    DocumentSearchResult, DocumentStatusResponse
)
from app.shared.storage.storage_service import StorageService
from app.shared.utils.file_hash import compute_sha256, generate_storage_path
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, StorageException
from app.shared.logging.logger import app_logger
from app.config import get_settings

# Celery tasks (imported lazily to avoid circular imports)
def get_process_document_task():
    from app.tasks.document_tasks import process_document
    return process_document

def get_reprocess_document_task():
    from app.tasks.document_tasks import reprocess_document
    return reprocess_document


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentRepository(session)
        self.storage = StorageService()
        self.settings = get_settings()

    async def upload(self, organization_id: UUID, uploaded_by: UUID, file_content: bytes,
                     original_filename: str, mime_type: str, request: DocumentUploadRequest) -> DocumentResponse:
        file_hash = compute_sha256(file_content)

        existing = await self.repo.get_by_hash(organization_id, file_hash)
        if existing:
            app_logger.info(f"Duplicate document detected", extra={
                "organization_id": str(organization_id),
                "file_hash": file_hash
            })
            return DocumentResponse.model_validate(existing)

        file_size = len(file_content)
        if file_size > self.settings.max_file_size_mb * 1024 * 1024:
            raise ValidationException(f"File size exceeds maximum allowed ({self.settings.max_file_size_mb}MB)")

        extension = os.path.splitext(original_filename)[1].lower()
        if extension not in self.settings.allowed_extensions:
            raise ValidationException(f"File type not allowed. Allowed: {self.settings.allowed_extensions}")

        storage_path = generate_storage_path(str(organization_id), original_filename)

        try:
            await self.storage.save(storage_path, file_content)
        except Exception as e:
            app_logger.error(f"Storage save failed", extra={"error": str(e)})
            raise StorageException("Failed to save file")

        document = Document(
            filename=os.path.basename(storage_path),
            original_filename=original_filename,
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type,
            extension=extension,
            document_type=request.document_type,
            organization_id=organization_id,
            uploaded_by=uploaded_by,
        )

        document = await self.repo.create(document)

        # Set initial status to PROCESSING
        document = await self.repo.update_status(
            document_id=document.id,
            status=DocumentStatus.PROCESSING
        )

        # Enqueue background processing task
        try:
            process_task = get_process_document_task()
            process_task.delay(str(document.id), str(organization_id))
            app_logger.info(f"Document processing task enqueued", extra={
                "document_id": str(document.id),
                "organization_id": str(organization_id)
            })
        except Exception as e:
            app_logger.error(f"Failed to enqueue processing task", extra={"document_id": str(document.id), "error": str(e)})
            document = await self.repo.update_status(
                document_id=document.id,
                status=DocumentStatus.FAILED,
                error_message=f"Failed to queue processing: {str(e)}"
            )

        app_logger.info(f"Document uploaded, processing queued", extra={
            "document_id": str(document.id),
            "organization_id": str(organization_id),
            "filename": original_filename,
            "status": document.status.value
        })

        return DocumentResponse.model_validate(document)

    async def get_by_id(self, document_id: UUID, organization_id: UUID) -> DocumentResponse:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id or document.is_deleted:
            raise ResourceNotFoundException("Document not found")
        return DocumentResponse.model_validate(document)

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = 20,
                   document_type: DocumentType = None, status: DocumentStatus = None) -> Tuple[List[DocumentResponse], int]:
        items, total = await self.repo.list(organization_id, page, page_size, document_type, status)
        return [DocumentResponse.model_validate(item) for item in items], total

    async def update_status(self, document_id: UUID, organization_id: UUID, status: DocumentStatus,
                            error_message: str = None, chunk_count: int = None,
                            vector_collection: str = None) -> DocumentResponse:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        document = await self.repo.update_status(document_id, status, error_message, chunk_count, vector_collection)
        return DocumentResponse.model_validate(document)

    async def delete(self, document_id: UUID, organization_id: UUID) -> None:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        try:
            await self.storage.delete(f"organizations/{organization_id}/documents/{document.filename}")
        except Exception as e:
            app_logger.warning(f"Storage delete failed", extra={"error": str(e)})

        await self.repo.soft_delete(document_id)
        app_logger.info(f"Document deleted", extra={"document_id": str(document_id)})

    async def get_status(self, document_id: UUID, organization_id: UUID) -> DocumentStatusResponse:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id or document.is_deleted:
            raise ResourceNotFoundException("Document not found")
        return DocumentStatusResponse.model_validate(document)

    async def reprocess(self, document_id: UUID, organization_id: UUID) -> DocumentResponse:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id or document.is_deleted:
            raise ResourceNotFoundException("Document not found")

        # Set status to PROCESSING
        document = await self.repo.update_status(document_id, DocumentStatus.PROCESSING)

        # Enqueue background reprocessing task
        try:
            reprocess_task = get_reprocess_document_task()
            reprocess_task.delay(str(document_id), str(organization_id))
            app_logger.info(f"Document reprocessing task enqueued", extra={
                "document_id": str(document_id),
                "organization_id": str(organization_id)
            })
        except Exception as e:
            app_logger.error(f"Failed to enqueue reprocessing task", extra={"document_id": str(document_id), "error": str(e)})
            document = await self.repo.update_status(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error_message=f"Failed to queue reprocessing: {str(e)}"
            )

        return DocumentResponse.model_validate(document)

    async def get_file_content(self, document_id: UUID, organization_id: UUID) -> Tuple[bytes, str, str]:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id or document.is_deleted:
            raise ResourceNotFoundException("Document not found")

        storage_path = f"organizations/{organization_id}/documents/{document.filename}"
        content = await self.storage.read(storage_path)
        return content, document.original_filename, document.mime_type

    async def verify_documents_exist(self, organization_id: UUID, document_ids: List[UUID]) -> bool:
        for doc_id in document_ids:
            doc = await self.repo.get_by_id(doc_id)
            if not doc or doc.organization_id != organization_id or doc.is_deleted:
                raise ValidationException(f"Document {doc_id} not found or not accessible")
        return True

    async def get_file_path(self, document_id: UUID, organization_id: UUID) -> str:
        document = await self.repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")
        return f"organizations/{organization_id}/documents/{document.filename}"