from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.modules.audit.repository import AuditRepository
from app.modules.audit.models import AuditLog, AuditAction
from app.modules.audit.schemas import AuditLogResponse, AuditLogListResponse, AuditFilterRequest
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException
from app.shared.logging.logger import app_logger


class AuditService:
    def __init__(self, session: AsyncSession):
        self.repo = AuditRepository(session)

    async def create_log(
        self,
        action: AuditAction,
        resource_type: str,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogResponse:
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            organization_id=organization_id,
            user_id=user_id,
        )
        audit_log = await self.repo.create(audit_log)
        app_logger.info(
            f"Audit log created",
            extra={
                "audit_log_id": str(audit_log.audit_log_id),
                "action": action.value,
                "resource_type": resource_type,
                "organization_id": str(organization_id),
            },
        )
        return AuditLogResponse.model_validate(audit_log)

    async def get_by_id(self, log_id: UUID, organization_id: UUID) -> AuditLogResponse:
        audit_log = await self.repo.get_by_id(log_id, organization_id)
        if not audit_log:
            raise ResourceNotFoundException("Audit log not found")
        return AuditLogResponse.model_validate(audit_log)

    async def list_logs(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> AuditLogListResponse:
        items, total = await self.repo.list(
            organization_id,
            page=page,
            page_size=page_size,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def filter_logs(
        self, organization_id: UUID, filters: AuditFilterRequest
    ) -> AuditLogListResponse:
        return await self.list_logs(
            organization_id=organization_id,
            page=filters.page,
            page_size=filters.page_size,
            action=filters.action,
            resource_type=filters.resource_type,
            resource_id=filters.resource_id,
            user_id=filters.user_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
        )