from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Tuple, Optional
from app.modules.chat.repository import ChatRepository
from app.modules.chat.models import ChatSession, ChatMessage, ChatSessionStatus
from app.modules.chat.schemas import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatSessionDetailResponse, ChatMessageCreate, ChatMessageResponse,
    ChatRequest, ChatResponse
)
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException
from app.shared.logging.logger import app_logger
from app.ai.facade import AIFacade


class ChatService:
    def __init__(self, session: AsyncSession):
        self.repo = ChatRepository(session)
        self.ai_facade = AIFacade()

    async def create_session(self, organization_id: UUID, created_by: UUID, request: ChatSessionCreate) -> ChatSessionResponse:
        session = ChatSession(
            title=request.title,
            organization_id=organization_id,
            created_by=created_by,
        )
        session = await self.repo.create(session)

        app_logger.info(f"Chat session created", extra={"session_id": str(session.chat_session_id)})
        return ChatSessionResponse.model_validate(session)

    async def get_session(self, session_id: UUID, organization_id: UUID) -> ChatSessionResponse:
        session = await self.repo.get_by_id(session_id, organization_id)
        if not session or session.is_deleted:
            raise ResourceNotFoundException("Chat session not found")
        return ChatSessionResponse.model_validate(session)

    async def get_session_detail(self, session_id: UUID, organization_id: UUID) -> ChatSessionDetailResponse:
        session = await self.repo.get_by_id_with_messages(session_id, organization_id)
        if not session or session.is_deleted:
            raise ResourceNotFoundException("Chat session not found")

        response = ChatSessionDetailResponse.model_validate(session)
        response.messages = [ChatMessageResponse.model_validate(m) for m in session.messages if not m.is_deleted]
        return response

    async def update_session(self, session_id: UUID, organization_id: UUID, request: ChatSessionUpdate) -> ChatSessionResponse:
        session = await self.repo.get_by_id(session_id, organization_id)
        if not session or session.is_deleted:
            raise ResourceNotFoundException("Chat session not found")

        if request.title is not None:
            session.title = request.title
        if request.status is not None:
            session.status = request.status

        session = await self.repo.update(session)
        return ChatSessionResponse.model_validate(session)

    async def send_message(self, session_id: UUID, organization_id: UUID, request: ChatRequest, current_user_id: UUID) -> ChatResponse:
        session = await self.repo.get_by_id(session_id, organization_id)
        if not session or session.is_deleted:
            raise ResourceNotFoundException("Chat session not found")

        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message,
        )
        await self.repo.add_message(user_message)

        context_doc_ids = None
        if request.context_document_ids:
            from uuid import UUID as UUIDType
            context_doc_ids = [UUIDType(d) for d in request.context_document_ids]

        ai_result = await self.ai_facade.chat(
            organization_id=organization_id,
            message=request.message,
            conversation_id=session_id,
            context_document_ids=context_doc_ids
        )

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_result["answer"],
            tokens_used=None,
            model_used=None,
        )
        await self.repo.add_message(assistant_message)

        session = await self.repo.update(session)

        return ChatResponse(
            message=ChatMessageResponse.model_validate(assistant_message),
            sources=ai_result.get("sources", []),
            confidence=ai_result.get("confidence", 0.0)
        )

    async def list_sessions(self, organization_id: UUID, page: int = 1, page_size: int = 20) -> Tuple[List[ChatSessionResponse], int]:
        items, total = await self.repo.list(organization_id, page, page_size)
        return [ChatSessionResponse.model_validate(item) for item in items], total

    async def delete_session(self, session_id: UUID, organization_id: UUID) -> None:
        session = await self.repo.get_by_id(session_id, organization_id)
        if not session:
            raise ResourceNotFoundException("Chat session not found")

        await self.repo.soft_delete(session_id, organization_id)
        app_logger.info(f"Chat session deleted", extra={"session_id": str(session_id)})