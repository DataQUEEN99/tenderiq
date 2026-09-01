from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.export.models import Export, ExportStatus
from app.shared.database.tenant_repository import TenantRepository
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ExportRepository(TenantRepository[Export]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Export, primary_key_attr='export_id')

    async def get_by_id(self, export_id: UUID, organization_id: UUID) -> Optional[Export]:
        return await super().get_by_id(export_id, organization_id)

    async def get_proposal_for_export(self, proposal_id: UUID, organization_id: UUID):
        from app.modules.proposal.models import Proposal
        result = await self.session.execute(
            select(Proposal).where(
                and_(Proposal.id == proposal_id, Proposal.organization_id == organization_id, Proposal.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, export: Export) -> Export:
        return await super().create(export)

    async def update(self, export: Export) -> Export:
        await self.session.flush()
        await self.session.refresh(export)
        return export

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Export], int]:
        return await super().list(organization_id, page, page_size)

    async def soft_delete(self, export_id: UUID, organization_id: UUID) -> bool:
        export = await self.get_by_id(export_id, organization_id)
        if not export:
            return False
        export.is_deleted = True
        await self.session.flush()
        return True