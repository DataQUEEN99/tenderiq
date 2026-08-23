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
    id: str
    title: Optional[str]
    status: ChatSessionStatus
    organization_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens_used: Optional[int]
    model_used: Optional[str]
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context_document_ids: List[str] = []


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence: float


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int