from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from app.shared.database.session import get_db
from app.modules.tender.service import TenderService
from app.modules.tender.schemas import (
    TenderCreate, TenderUpdate, TenderStatusUpdate,
    TenderDocumentAttach, TenderResponse, TenderDetailResponse, TenderListResponse,
    TenderSummaryCreate, TenderSummaryResponse,
    EligibilityAnalysisCreate, EligibilityAnalysisResponse,
    ComplianceMatrixCreate, ComplianceMatrixResponse
)
from app.modules.tender.models import TenderStatus
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission
from app.modules.tender.ai_api import router as ai_router


router = APIRouter(prefix="/tenders", tags=["Tenders"])
router.include_router(ai_router)


@router.post("", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
async def create_tender(
    request: TenderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_CREATE)),
):
    service = TenderService(db)
    return await service.create(current_user.organization_id, current_user.user_id, request)


@router.get("/{tender_id}", response_model=TenderResponse)
async def get_tender(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.get_by_id(tender_id, current_user.organization_id)


@router.get("/{tender_id}/detail", response_model=TenderDetailResponse)
async def get_tender_detail(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.get_detail(tender_id, current_user.organization_id)


@router.put("/{tender_id}", response_model=TenderResponse)
async def update_tender(
    tender_id: UUID,
    request: TenderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_UPDATE)),
):
    service = TenderService(db)
    return await service.update(tender_id, current_user.organization_id, request)


@router.patch("/{tender_id}/status", response_model=TenderResponse)
async def update_tender_status(
    tender_id: UUID,
    request: TenderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_STATUS)),
):
    service = TenderService(db)
    return await service.update_status(tender_id, current_user.organization_id, request)


@router.post("/{tender_id}/documents", response_model=List[str], status_code=status.HTTP_201_CREATED)
async def attach_documents(
    tender_id: UUID,
    request: TenderDocumentAttach,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_DOC_ATTACH)),
):
    from uuid import UUID as UUIDType
    doc_ids = [UUIDType(d) for d in request.document_ids]
    service = TenderService(db)
    return await service.attach_documents(tender_id, current_user.organization_id, doc_ids)


@router.get("/{tender_id}/documents")
async def list_tender_documents(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    docs = await service.repo.get_attached_documents(tender_id, current_user.organization_id)
    return [
        {
            "id": str(td.tender_document_id),
            "tender_id": str(td.tender_id),
            "document_id": str(td.document_id),
            "created_at": td.created_at.isoformat() if td.created_at else None,
            "updated_at": td.updated_at.isoformat() if td.updated_at else None,
            "document": {
                "id": str(td.document.document_id),
                "document_id": str(td.document.document_id),
                "original_filename": td.document.original_filename,
                "filename": td.document.filename,
                "file_size": td.document.file_size,
                "mime_type": td.document.mime_type,
                "extension": td.document.extension,
                "status": td.document.status.value if hasattr(td.document.status, "value") else str(td.document.status),
                "created_at": td.document.created_at.isoformat() if td.document.created_at else None,
            } if td.document else None
        }
        for td in docs
    ]


@router.delete("/{tender_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_document(
    tender_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_DOC_DETACH)),
):
    service = TenderService(db)
    await service.detach_document(tender_id, current_user.organization_id, document_id)


@router.get("", response_model=TenderListResponse)
async def list_tenders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TenderStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status=status,
        search=search
    )
    return TenderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_DELETE)),
):
    service = TenderService(db)
    await service.delete(tender_id, current_user.organization_id)