from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.shared.database.session import get_db
from app.modules.proposal.service import ProposalService
from app.modules.proposal.schemas import (
    ProposalCreate, ProposalUpdate, ProposalStatusUpdate,
    ProposalSectionCreate, ProposalSectionUpdate,
    ProposalResponse, ProposalDetailResponse, ProposalListResponse,
    ProposalGenerateRequest
)
from app.modules.proposal.models import ProposalStatus
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission


router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    request: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_GENERATE)),
):
    service = ProposalService(db)
    return await service.create(current_user.organization_id, current_user.id, request)


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_READ)),
):
    service = ProposalService(db)
    return await service.get_by_id(proposal_id, current_user.organization_id)


@router.get("/{proposal_id}/detail", response_model=ProposalDetailResponse)
async def get_proposal_detail(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_READ)),
):
    service = ProposalService(db)
    return await service.get_detail(proposal_id, current_user.organization_id)


@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: UUID,
    request: ProposalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    service = ProposalService(db)
    return await service.update(proposal_id, current_user.organization_id, request)


@router.patch("/{proposal_id}/status", response_model=ProposalResponse)
async def update_proposal_status(
    proposal_id: UUID,
    request: ProposalStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_VERSION)),
):
    service = ProposalService(db)
    return await service.update_status(proposal_id, current_user.organization_id, request)


@router.post("/{proposal_id}/sections", response_model=ProposalSectionCreate, status_code=status.HTTP_201_CREATED)
async def create_section(
    proposal_id: UUID,
    request: ProposalSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    service = ProposalService(db)
    return await service.create_section(proposal_id, current_user.organization_id, request)


@router.put("/{proposal_id}/sections/{section_id}")
async def update_section(
    proposal_id: UUID,
    section_id: UUID,
    request: ProposalSectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    service = ProposalService(db)
    return await service.update_section(proposal_id, current_user.organization_id, section_id, request)


@router.delete("/{proposal_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    proposal_id: UUID,
    section_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    service = ProposalService(db)
    await service.delete_section(proposal_id, current_user.organization_id, section_id)


@router.post("/{proposal_id}/generate")
async def generate_proposal(
    proposal_id: UUID,
    request: ProposalGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_GENERATE)),
):
    service = ProposalService(db)
    return await service.generate(proposal_id, current_user.organization_id, request.company_profile, request.requirements)


@router.post("/{proposal_id}/documents", response_model=List[str], status_code=status.HTTP_201_CREATED)
async def attach_documents(
    proposal_id: UUID,
    document_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    from uuid import UUID as UUIDType
    doc_ids = [UUIDType(d) for d in document_ids]
    service = ProposalService(db)
    return await service.attach_documents(proposal_id, current_user.organization_id, doc_ids)


@router.delete("/{proposal_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_document(
    proposal_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_UPDATE)),
):
    service = ProposalService(db)
    await service.detach_document(proposal_id, current_user.organization_id, document_id)


@router.get("", response_model=ProposalListResponse)
async def list_proposals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ProposalStatus] = Query(None),
    tender_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_READ)),
):
    service = ProposalService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status=status,
        tender_id=tender_id
    )
    return ProposalListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROPOSAL_VERSION)),
):
    service = ProposalService(db)
    await service.delete(proposal_id, current_user.organization_id)