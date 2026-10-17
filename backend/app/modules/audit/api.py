from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.shared.database.session import get_db
from app.modules.audit.service import AuditService
from app.modules.audit.schemas import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditFilterRequest,
)
from app.modules.audit.models import AuditAction
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    audit_action = None
    if action and action.lower() != "all":
        try:
            audit_action = AuditAction(action.upper())
        except ValueError:
            pass

    res_type = None
    if resource_type and resource_type.lower() != "all":
        res_type = resource_type

    service = AuditService(db)
    return await service.list_logs(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        action=audit_action,
        resource_type=res_type,
        resource_id=resource_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/logs/filter", response_model=AuditLogListResponse)
async def filter_audit_logs(
    filters: AuditFilterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    service = AuditService(db)
    return await service.filter_logs(
        organization_id=current_user.organization_id,
        filters=filters,
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    service = AuditService(db)
    return await service.get_by_id(log_id, current_user.organization_id)