from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.chat.models import ChatSession, ChatMessage, ChatContext, ChatSessionStatus
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, session_id: UUID) -> Optional[ChatSession]:
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_messages(self, session_id: UUID) -> Optional[ChatSession]:
        result = await self.session.execute(
            select(ChatSession)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.contexts)
            )
            .where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def create(self, session: ChatSession) -> ChatSession:
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def update(self, session: ChatSession) -> ChatSession:
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[ChatSession], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        result = await self.session.execute(
            select(ChatSession).where(
                and_(ChatSession.organization_id == organization_id, ChatSession.is_deleted == False)
            ).order_by(desc(ChatSession.updated_at)).offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        count_result = await self.session.execute(
            select(func.count(ChatSession.id)).where(
                and_(ChatSession.organization_id == organization_id, ChatSession.is_deleted == False)
            )
        )
        total = count_result.scalar_one()

        return list(items), total

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_messages(self, session_id: UUID, limit: int = 50) -> List[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at)).limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def add_context(self, context: ChatContext) -> ChatContext:
        self.session.add(context)
        await self.session.flush()
        await self.session.refresh(context)
        return context

    async def get_contexts(self, session_id: UUID) -> List[ChatContext]:
        result = await self.session.execute(
            select(ChatContext).where(ChatContext.session_id == session_id)
        )
        return result.scalars().all()

    async def soft_delete(self, session_id: UUID) -> bool:
        session = await self.get_by_id(session_id)
        if not session:
            return False
        session.is_deleted = True
        session.status = ChatSessionStatus.ARCHIVED
        await self.session.flush()
        return True