from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
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
from app.modules.tender.models import TenderSummary, EligibilityAnalysis
from app.shared.security.auth_dependencies import require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException

router = APIRouter(prefix="", tags=["Tenders - AI Outputs"])


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
        summary_text=request.summary_text,
        generation_model=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms,
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
        overall_eligible=request.overall_eligible,
        eligibility_score=request.eligibility_score,
        criteria_results=request.criteria_results,
        missing_requirements=request.missing_requirements,
        generation_model=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms,
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
        overall_compliance_score=request.overall_compliance_score,
        requirement_results=request.requirement_results,
        mandatory_met=request.mandatory_met,
        mandatory_total=request.mandatory_total,
        desirable_met=request.desirable_met,
        desirable_total=request.desirable_total,
        generation_model=request.model_used,
        prompt_hash=request.prompt_hash,
        tokens_used=request.tokens_used,
        generation_latency_ms=request.generation_latency_ms,
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