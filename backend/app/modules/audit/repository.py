from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from datetime import datetime
from app.modules.audit.models import AuditLog, AuditAction
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        result = await self.session.execute(select(AuditLog).where(AuditLog.id == log_id))
        return result.scalar_one_or_none()

    async def create(self, audit_log: AuditLog) -> AuditLog:
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def list(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        organization_id: Optional[UUID] = None,
    ) -> tuple[List[AuditLog], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        conditions = [AuditLog.is_deleted == False]
        if organization_id:
            conditions.append(AuditLog.organization_id == organization_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        query = select(AuditLog).where(and_(*conditions)).order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(AuditLog.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total