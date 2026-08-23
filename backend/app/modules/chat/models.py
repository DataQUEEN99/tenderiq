from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


class ChatSessionStatus(str, enum.Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    title = Column(String(255), nullable=True)
    status = Column(SQLEnum(ChatSessionStatus), nullable=False, default=ChatSessionStatus.ACTIVE)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization")
    creator = relationship("User")

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    contexts = relationship("ChatContext", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)

    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    session = relationship("ChatSession", back_populates="messages")


class ChatContext(BaseModel):
    __tablename__ = "chat_contexts"

    context_type = Column(String(50), nullable=False)  # tender, proposal, document, company
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON string

    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    session = relationship("ChatSession", back_populates="contexts")