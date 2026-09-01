from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
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


# TenderSummary endpoints
@router.post("/{tender_id}/summary", response_model=TenderSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_tender_summary(
    tender_id: UUID,
    request: TenderSummaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.create_summary(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        summary_type=request.summary_type,
        summary_text=request.summary_text,
        model_used=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms,
        source_document_ids=request.source_document_ids
    )


@router.get("/{tender_id}/summary", response_model=TenderSummaryResponse)
async def get_tender_summary(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.get_summary(current_user.organization_id, tender_id)


# EligibilityAnalysis endpoints
@router.post("/{tender_id}/eligibility", response_model=EligibilityAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_eligibility_analysis(
    tender_id: UUID,
    request: EligibilityAnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.create_eligibility_analysis(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        company_profile_id=UUID(request.company_profile_id),
        overall_eligible=request.overall_eligible,
        eligibility_score=request.eligibility_score,
        criteria_results=request.criteria_results,
        missing_requirements=request.missing_requirements,
        model_used=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms
    )


@router.get("/{tender_id}/eligibility", response_model=EligibilityAnalysisResponse)
async def get_eligibility_analysis(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.get_eligibility_analysis(current_user.organization_id, tender_id)


# ComplianceMatrix endpoints
@router.post("/{tender_id}/compliance", response_model=ComplianceMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_matrix(
    tender_id: UUID,
    request: ComplianceMatrixCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.create_compliance_matrix(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        proposal_id=UUID(request.proposal_id),
        overall_compliance_score=request.overall_compliance_score,
        mandatory_met=request.mandatory_met,
        mandatory_total=request.mandatory_total,
        desirable_met=request.desirable_met,
        desirable_total=request.desirable_total,
        requirement_results=request.requirement_results,
        model_used=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms
    )


@router.get("/{tender_id}/compliance", response_model=ComplianceMatrixResponse)
async def get_compliance_matrix(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderService(db)
    return await service.get_compliance_matrix(current_user.organization_id, tender_id)