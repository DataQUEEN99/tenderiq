from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.authentication.models import User
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from datetime import datetime, timedelta


class UserManagementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users_by_org(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[User], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        result = await self.session.execute(
            select(User).where(
                and_(User.organization_id == organization_id, User.is_deleted == False)
            ).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        count_result = await self.session.execute(
            select(func.count(User.user_id)).where(
                and_(User.organization_id == organization_id, User.is_deleted == False)
            )
        )
        total = count_result.scalar_one()

        return list(items), total

    async def get_user_by_id(self, user_id: UUID, organization_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(
                and_(User.user_id == user_id, User.organization_id == organization_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_email_in_org(self, email: str, organization_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(
                and_(User.email == email, User.organization_id == organization_id, User.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update user entity - flush and refresh"""
        await self.session.flush()
        await self.session.refresh(user)
        return user