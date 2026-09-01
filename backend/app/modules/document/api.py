from fastapi import APIRouter, Depends, status, UploadFile, File, Query, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.shared.database.session import get_db
from app.modules.document.service import DocumentService
from app.modules.document.schemas import (
    DocumentUploadRequest, DocumentResponse, DocumentListResponse,
    DocumentStatusUpdate, DocumentStatusResponse, DocumentSearchRequest, DocumentSearchResult,
    DocumentProgressResponse
)
from app.modules.document.models import DocumentStatus, DocumentType
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission
from app.shared.exceptions.custom_exceptions import ValidationException
from app.shared.logging.logger import app_logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_UPLOAD)),
):
    file_content = await file.read()
    if not file_content:
        raise ValidationException("Empty file uploaded")

    mime_type = file.content_type or "application/octet-stream"

    request = DocumentUploadRequest(document_type=document_type)
    service = DocumentService(db)

    return await service.upload(
        organization_id=current_user.organization_id,
        uploaded_by=current_user.id,
        file_content=file_content,
        original_filename=file.filename,
        mime_type=mime_type,
        request=request
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
):
    service = DocumentService(db)
    return await service.get_by_id(document_id, current_user.organization_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
):
    service = DocumentService(db)
    return await service.get_status(document_id, current_user.organization_id)


@router.get("/{document_id}/progress", response_model=DocumentProgressResponse)
async def get_document_progress(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
):
    """Get real-time processing progress for a document."""
    from app.modules.document.repository import DocumentProcessingRepository
    from app.modules.document.models import Document

    # Verify document exists and belongs to user's org
    doc = await db.get(Document, document_id)
    if not doc or doc.organization_id != current_user.organization_id or doc.is_deleted:
        raise ValidationException("Document not found")

    # Get processing record
    proc_repo = DocumentProcessingRepository(db)
    processing = await proc_repo.get_by_document_id(document_id)

    if not processing:
        return DocumentProgressResponse(
            document_id=str(document_id),
            stage="pending",
            status="pending",
            progress=0
        )

    return DocumentProgressResponse(
        document_id=str(document_id),
        stage=processing.stage,
        status=processing.status,
        progress=processing.progress,
        error_message=processing.error_message,
        started_at=processing.started_at,
        completed_at=processing.completed_at
    )


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_REPROCESS)),
):
    service = DocumentService(db)
    return await service.reprocess(document_id, current_user.organization_id)


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_DOWNLOAD)),
):
    service = DocumentService(db)
    content, filename, mime_type = await service.get_file_content(document_id, current_user.organization_id)
    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: Optional[DocumentType] = Query(None),
    document_status: Optional[DocumentStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
):
    service = DocumentService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        document_type=document_type,
        status=document_status
    )
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    document_id: UUID,
    request: DocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_UPDATE)),
):
    service = DocumentService(db)
    return await service.update_status(
        document_id=document_id,
        organization_id=current_user.organization_id,
        status=request.status,
        error_message=request.error_message,
        chunk_count=request.chunk_count,
        vector_collection=request.vector_collection
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_DELETE)),
):
    service = DocumentService(db)
    await service.delete(document_id, current_user.organization_id)


@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    request: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
):
    from app.ai.facade import AIFacade
    facade = AIFacade()
    results = await facade.search_documents(
        organization_id=current_user.organization_id,
        query=request.query,
        document_type=request.document_type,
        top_k=request.page_size
    )
    return results