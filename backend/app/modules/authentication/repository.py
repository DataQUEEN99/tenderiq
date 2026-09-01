from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from app.modules.authentication.models import User, UserRole
from app.shared.database.base import BaseModel


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_first_admin(self) -> Optional[User]:
        """Get the first admin user in the system (for bootstrap idempotency)"""
        result = await self.session.execute(
            select(User).where(User.role == UserRole.ADMIN).order_by(User.created_at).limit(1)
        )
        return result.scalar_one_or_none()

    async def count_users(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(select(func.count(User.user_id)))
        return result.scalar_one()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Update user entity - flush and refresh"""
        await self.session.flush()
        await self.session.refresh(user)
        return user