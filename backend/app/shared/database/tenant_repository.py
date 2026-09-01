from typing import TypeVar, Generic, Optional, List, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import InstrumentedAttribute
from app.shared.database.base import BaseModel


T = TypeVar('T', bound=BaseModel)


class TenantRepository(Generic[T]):
    """
    Base repository class that enforces tenant (organization) isolation.
    All queries automatically filter by organization_id to prevent cross-tenant data access.
    """

    def __init__(self, session: AsyncSession, model: Type[T],
                 organization_id_attr: InstrumentedAttribute = None,
                 primary_key_attr: str = 'id'):
        self.session = session
        self.model = model
        # Default to 'organization_id' attribute, can be overridden
        self.organization_id_attr = organization_id_attr or getattr(model, 'organization_id', None)
        # Primary key attribute name (e.g., 'organization_id', 'user_id', 'tender_id', etc.)
        self.primary_key_attr = primary_key_attr

    def _tenant_filter(self, organization_id: UUID):
        """Create a filter condition for tenant isolation"""
        if self.organization_id_attr is not None:
            return self.organization_id_attr == organization_id
        return None

    def _pk_filter(self, id: UUID):
        """Create a filter condition for primary key"""
        return getattr(self.model, self.primary_key_attr) == id

    async def get_by_id(self, id: UUID, organization_id: UUID) -> Optional[T]:
        """Get entity by ID with tenant isolation"""
        query = select(self.model).where(self._pk_filter(id))
        tenant_filter = self._tenant_filter(organization_id)
        if tenant_filter is not None:
            query = query.where(tenant_filter)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_unscoped(self, id: UUID) -> Optional[T]:
        """Get entity by ID WITHOUT tenant isolation - use with caution"""
        result = await self.session.execute(select(self.model).where(self._pk_filter(id)))
        return result.scalar_one_or_none()

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = 20,
                   **filters) -> tuple[List[T], int]:
        """List entities with tenant isolation and pagination"""
        from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(self.model)
        tenant_filter = self._tenant_filter(organization_id)
        if tenant_filter is not None:
            query = query.where(tenant_filter)

        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        # Soft delete filter
        if hasattr(self.model, 'is_deleted'):
            query = query.where(self.model.is_deleted == False)

        query = query.order_by(self.model.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        # Count query
        pk_col = getattr(self.model, self.primary_key_attr)
        count_query = select(func.count(pk_col))
        if tenant_filter is not None:
            count_query = count_query.where(tenant_filter)
        if hasattr(self.model, 'is_deleted'):
            count_query = count_query.where(self.model.is_deleted == False)

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                count_query = count_query.where(getattr(self.model, key) == value)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def create(self, entity: T) -> T:
        """Create new entity"""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Update existing entity"""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def soft_delete(self, id: UUID, organization_id: UUID) -> bool:
        """Soft delete entity with tenant isolation"""
        entity = await self.get_by_id(id, organization_id)
        if not entity:
            return False
        if hasattr(entity, 'is_deleted'):
            entity.is_deleted = True
        await self.session.flush()
        return True

    async def hard_delete(self, id: UUID, organization_id: UUID) -> bool:
        """Hard delete entity with tenant isolation"""
        entity = await self.get_by_id(id, organization_id)
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True