from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List
from app.shared.database.session import get_db
from app.modules.chat.service import ChatService
from app.modules.chat.schemas import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatSessionDetailResponse, ChatMessageResponse,
    ChatRequest, ChatResponse, ChatSessionListResponse
)
from app.modules.chat.models import ChatSessionStatus
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_CREATE)),
):
    service = ChatService(db)
    return await service.create_session(current_user.organization_id, current_user.user_id, request)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_READ)),
):
    service = ChatService(db)
    return await service.get_session(session_id, current_user.organization_id)


@router.get("/sessions/{session_id}/detail", response_model=ChatSessionDetailResponse)
async def get_session_detail(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_READ)),
):
    service = ChatService(db)
    return await service.get_session_detail(session_id, current_user.organization_id)


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: UUID,
    request: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_CREATE)),
):
    service = ChatService(db)
    return await service.update_session(session_id, current_user.organization_id, request)


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_MESSAGE)),
):
    service = ChatService(db)
    return await service.send_message(session_id, current_user.organization_id, request, current_user.user_id)


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_READ)),
):
    service = ChatService(db)
    items, total = await service.list_sessions(current_user.organization_id, page, page_size)
    return ChatSessionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CHAT_CREATE)),
):
    service = ChatService(db)
    await service.delete_session(session_id, current_user.organization_id)