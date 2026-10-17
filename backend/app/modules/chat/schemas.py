from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.modules.chat.models import ChatSessionStatus


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    context_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[ChatSessionStatus] = None


class ChatSessionResponse(BaseModel):
    chat_session_id: UUID
    id: Optional[UUID] = None
    title: Optional[str] = None
    status: ChatSessionStatus
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    def model_post_init(self, __context: Any) -> None:
        if self.id is None:
            self.id = self.chat_session_id

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    chat_message_id: UUID
    id: Optional[UUID] = None
    role: str
    content: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    session_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    def model_post_init(self, __context: Any) -> None:
        if self.id is None:
            self.id = self.chat_message_id
        if self.updated_at is None:
            self.updated_at = self.created_at

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context_document_ids: List[str] = []


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    sources: List[Dict[str, Any]] = []
    confidence: float


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int