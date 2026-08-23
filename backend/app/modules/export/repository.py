from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.export.models import Export, ExportStatus
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ExportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, export_id: UUID) -> Optional[Export]:
        result = await self.session.execute(
            select(Export).where(Export.id == export_id)
        )
        return result.scalar_one_or_none()

    async def get_proposal_for_export(self, proposal_id: UUID, organization_id: UUID):
        from app.modules.proposal.models import Proposal
        result = await self.session.execute(
            select(Proposal).where(
                and_(Proposal.id == proposal_id, Proposal.organization_id == organization_id, Proposal.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, export: Export) -> Export:
        self.session.add(export)
        await self.session.flush()
        await self.session.refresh(export)
        return export

    async def update(self, export: Export) -> Export:
        await self.session.flush()
        await self.session.refresh(export)
        return export

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[Export], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        result = await self.session.execute(
            select(Export).where(
                and_(Export.organization_id == organization_id, Export.is_deleted == False)
            ).order_by(desc(Export.created_at)).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        count_result = await self.session.execute(
            select(func.count(Export.id)).where(
                and_(Export.organization_id == organization_id, Export.is_deleted == False)
            )
        )
        total = count_result.scalar_one()

        return list(items), total

    async def soft_delete(self, export_id: UUID) -> bool:
        export = await self.get_by_id(export_id)
        if not export:
            return False
        export.is_deleted = True
        await self.session.flush()
        return True