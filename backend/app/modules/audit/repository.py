from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from datetime import datetime
from app.modules.audit.models import AuditLog, AuditAction
from app.shared.database.tenant_repository import TenantRepository
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class AuditRepository(TenantRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog, primary_key_attr='audit_log_id')

    async def get_by_id(self, log_id: UUID, organization_id: UUID) -> Optional[AuditLog]:
        return await super().get_by_id(log_id, organization_id)

    async def create(self, audit_log: AuditLog) -> AuditLog:
        return await super().create(audit_log)

    async def list(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[AuditLog], int]:
        return await super().list(
            organization_id,
            page,
            page_size,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )