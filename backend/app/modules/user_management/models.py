from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
from app.modules.authentication.models import UserRole


class UserInvitation(BaseModel):
    __tablename__ = "user_invitations"

    email = Column(String(255), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.MEMBER)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])