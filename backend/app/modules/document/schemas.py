from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.modules.document.models import DocumentStatus, DocumentType


class DocumentUploadRequest(BaseModel):
    document_type: DocumentType = DocumentType.OTHER


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_hash: str
    file_size: int
    mime_type: str
    extension: str
    document_type: DocumentType
    status: DocumentStatus
    error_message: Optional[str]
    chunk_count: int
    vector_collection: Optional[str]
    organization_id: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    vector_collection: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    id: str
    status: DocumentStatus
    chunk_count: int
    vector_collection: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_type: Optional[DocumentType] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class DocumentSearchResult(BaseModel):
    document: DocumentResponse
    relevance_score: float
    matched_chunks: List[str]