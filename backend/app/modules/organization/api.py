from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.session import get_db
from app.modules.organization.service import OrganizationService
from app.modules.organization.schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationStatusUpdate,
    OrganizationResponse, OrganizationListResponse
)
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User, UserRole
from app.shared.security.permissions import Permission
from app.shared.exceptions.custom_exceptions import PermissionDeniedException


router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _verify_tenant_access(current_user: User, org_id: UUID):
    if current_user.role != UserRole.ADMIN and current_user.organization_id != org_id:
        raise PermissionDeniedException("Access denied to organization outside tenant boundary.")


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_CREATE)),
):
    service = OrganizationService(db)
    return await service.create(request)


@router.get("/me", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)
    return await service.get_by_id(current_user.organization_id)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_READ)),
):
    _verify_tenant_access(current_user, org_id)
    service = OrganizationService(db)
    return await service.get_by_id(organization_id)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    request: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_UPDATE)),
):
    _verify_tenant_access(current_user, org_id)
    service = OrganizationService(db)
    return await service.update(organization_id, request)


@router.patch("/{organization_id}/status", response_model=OrganizationResponse)
async def update_organization_status(
    organization_id: UUID,
    request: OrganizationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_UPDATE)),
):
    _verify_tenant_access(current_user, org_id)
    service = OrganizationService(db)
    return await service.update_status(organization_id, request)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_READ)),
):
    service = OrganizationService(db)
    items, total = await service.list(page, page_size)
    return OrganizationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORG_DELETE)),
):
    _verify_tenant_access(current_user, org_id)
    service = OrganizationService(db)
    await service.soft_delete(organization_id)