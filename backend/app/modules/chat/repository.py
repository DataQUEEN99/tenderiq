from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.modules.chat.models import ChatSession, ChatMessage, ChatSessionStatus
from app.shared.database.tenant_repository import TenantRepository
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ChatRepository(TenantRepository[ChatSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ChatSession, primary_key_attr='chat_session_id')

    async def get_by_id(self, session_id: UUID, organization_id: UUID) -> Optional[ChatSession]:
        return await super().get_by_id(session_id, organization_id)

    async def get_by_id_with_messages(self, session_id: UUID, organization_id: UUID) -> Optional[ChatSession]:
        result = await self.session.execute(
            select(ChatSession)
            .options(
                selectinload(ChatSession.messages)
            )
            .where(and_(ChatSession.chat_session_id == session_id, ChatSession.organization_id == organization_id))
        )
        return result.scalar_one_or_none()

    async def create(self, session: ChatSession) -> ChatSession:
        return await super().create(session)

    async def update(self, session: ChatSession) -> ChatSession:
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[ChatSession], int]:
        return await super().list(organization_id, page, page_size)

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

    async def soft_delete(self, session_id: UUID, organization_id: UUID) -> bool:
        session = await self.get_by_id(session_id, organization_id)
        if not session:
            return False
        session.is_deleted = True
        session.status = ChatSessionStatus.ARCHIVED
        await self.session.flush()
        return True