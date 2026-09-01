from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.modules.document.models import DocumentStatus, DocumentType
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID


class DocumentUploadRequest(BaseModel):
    document_type: DocumentType = DocumentType.OTHER


class DocumentResponse(BaseModel):
    document_id: str
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


# CompanyDocument schemas
class CompanyDocumentResponse(BaseModel):
    company_document_id: str
    company_profile_id: str
    document_id: str
    relationship_type: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyDocumentListResponse(BaseModel):
    items: List[CompanyDocumentResponse]
    total: int
    page: int
    page_size: int


# DocumentContent schemas
class DocumentContentResponse(BaseModel):
    document_content_id: str
    document_id: str
    extracted_text: Optional[str]
    extraction_method: str
    extraction_status: str
    error_message: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    character_count: Optional[int]
    extracted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# DocumentProcessing schemas
class DocumentProcessingResponse(BaseModel):
    document_processing_id: str
    document_id: str
    stage: str
    status: str
    progress: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentProgressResponse(BaseModel):
    document_id: str
    stage: str
    status: str
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None