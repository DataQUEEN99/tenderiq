from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.shared.database.session import get_db
from app.modules.tender.ai_services import (
    TenderSummaryService, EligibilityAnalysisService,
    ComplianceMatrixService
)
from app.modules.tender.schemas import (
    TenderSummaryCreate, TenderSummaryResponse,
    EligibilityAnalysisCreate, EligibilityAnalysisResponse,
    ComplianceMatrixCreate, ComplianceMatrixResponse
)
from app.modules.tender.models import TenderSummary, EligibilityAnalysis, ComplianceMatrix
from app.shared.security.auth_dependencies import require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException

router = APIRouter(prefix="/tenders", tags=["Tenders - AI Outputs"])


# Tender Summary endpoints
@router.post("/{tender_id}/summary", response_model=TenderSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_tender_summary(
    tender_id: UUID,
    request: TenderSummaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderSummaryService(db)
    return await service.create_summary(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        summary_type=request.summary_type,
        content=request.content,
        generation_model=request.generation_model,
        generation_prompt=request.generation_prompt,
        metadata=request.metadata,
    )


@router.get("/{tender_id}/summary", response_model=TenderSummaryResponse)
async def get_tender_summary(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderSummaryService(db)
    summary = await service.get_summary(current_user.organization_id, tender_id)
    if not summary:
        raise ResourceNotFoundException("Tender summary not found")
    return summary


@router.get("/{tender_id}/summaries", response_model=List[TenderSummaryResponse])
async def list_tender_summaries(
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = TenderSummaryService(db)
    items, total = await service.list_summaries(current_user.organization_id, page, page_size)
    return items


# Eligibility Analysis endpoints
@router.post("/{tender_id}/eligibility", response_model=EligibilityAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_eligibility_analysis(
    tender_id: UUID,
    request: EligibilityAnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = EligibilityAnalysisService(db)
    return await service.create_analysis(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        company_profile_id=UUID(request.company_profile_id),
        is_eligible=request.is_eligible,
        eligibility_score=request.eligibility_score,
        mandatory_requirements=request.mandatory_requirements,
        optional_requirements=request.optional_requirements,
        gaps=request.gaps,
        recommendations=request.recommendations,
        generation_model=request.generation_model,
        generation_prompt=request.generation_prompt,
        metadata=request.metadata,
    )


@router.get("/{tender_id}/eligibility", response_model=EligibilityAnalysisResponse)
async def get_eligibility_analysis(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = EligibilityAnalysisService(db)
    analysis = await service.get_analysis(current_user.organization_id, tender_id)
    if not analysis:
        raise ResourceNotFoundException("Eligibility analysis not found")
    return analysis


@router.get("/eligibility-analyses", response_model=List[EligibilityAnalysisResponse])
async def list_eligibility_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = EligibilityAnalysisService(db)
    items, total = await service.list_analyses(current_user.organization_id, page, page_size)
    return items


# Compliance Matrix endpoints
@router.post("/{tender_id}/compliance", response_model=ComplianceMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_matrix(
    tender_id: UUID,
    request: ComplianceMatrixCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = ComplianceMatrixService(db)
    return await service.create_matrix(
        organization_id=current_user.organization_id,
        tender_id=tender_id,
        proposal_id=UUID(request.proposal_id),
        compliance_score=request.compliance_score,
        requirements=request.requirements,
        non_compliant_items=request.non_compliant_items,
        partially_compliant_items=request.partially_compliant_items,
        generation_model=request.generation_model,
        generation_prompt=request.generation_prompt,
        metadata=request.metadata,
    )


@router.get("/{tender_id}/compliance", response_model=ComplianceMatrixResponse)
async def get_compliance_matrix(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = ComplianceMatrixService(db)
    matrix = await service.get_matrix(current_user.organization_id, tender_id)
    if not matrix:
        raise ResourceNotFoundException("Compliance matrix not found")
    return matrix


@router.get("/compliance-matrices", response_model=List[ComplianceMatrixResponse])
async def list_compliance_matrices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TENDER_READ)),
):
    service = ComplianceMatrixService(db)
    items, total = await service.list_matrices(current_user.organization_id, page, page_size)
    return items