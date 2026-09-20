import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.shared.storage.storage_service import StorageService
from app.ai.ingestion.text_extractor import TextExtractor
from app.ai.ingestion.chunker import Chunker
from app.ai.ingestion.embedding_generator import EmbeddingGenerator
from app.ai.ingestion.vector_indexer import VectorIndexer
from app.modules.document.repository import DocumentRepository
from app.modules.document.models import Document, DocumentStatus, DocumentType
from app.modules.document.ai_services import DocumentContentService, DocumentProcessingService
from app.shared.logging.logger import app_logger
from app.config import get_settings


class DocumentProcessingPipeline:
    """Orchestrates the complete document processing pipeline:
    text extraction -> chunking -> embedding -> vector indexing -> persistence"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.storage = StorageService()
        self.text_extractor = TextExtractor()
        self.chunker = Chunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_indexer = VectorIndexer()
        self.doc_repo = DocumentRepository(session)
        self.processing_service = DocumentProcessingService(session)
        self.content_service = DocumentContentService(session)

    async def process_document(self, document_id: UUID, organization_id: UUID) -> dict:
        """Process a document through the complete pipeline"""
        # Get document
        document = await self.doc_repo.get_by_id(document_id, organization_id)
        if not document:
            raise ValueError("Document not found")

        # Get file path
        file_path = self.storage.get_full_path(
            f"organizations/{organization_id}/documents/{document.filename}"
        )

        # Start processing
        await self.processing_service.start_processing(document_id, organization_id)

        try:
            # Step 1: Extract text
            await self.processing_service.update_progress(document_id, organization_id, "text_extraction", 10)
            app_logger.info(f"Extracting text from document", extra={"document_id": str(document_id)})
            text = await self.text_extractor.extract(file_path, document.mime_type)

            if not text or not text.strip():
                raise ValueError("No text content extracted from document")

            # Save content
            char_count = len(text)
            page_count = None
            extraction_method = "pymupdf" if document.mime_type == "application/pdf" else "native"

            if document.mime_type == "application/pdf":
                import fitz
                doc = fitz.open(file_path)
                page_count = doc.page_count
                doc.close()

            await self.content_service.save_content(
                document_id=document_id,
                organization_id=organization_id,
                text_content=text,
                page_count=page_count,
                char_count=char_count,
                extraction_method=extraction_method,
            )

            # Step 2: Chunk text
            await self.processing_service.update_progress(document_id, organization_id, "chunking", 30)
            app_logger.info(f"Chunking text", extra={"document_id": str(document_id)})
            chunks = self.chunker.chunk(text)

            if not chunks:
                raise ValueError("No chunks generated from document")

            # Step 3: Generate embeddings
            await self.processing_service.update_progress(document_id, organization_id, "embedding_generation", 50)
            app_logger.info(f"Generating embeddings for {len(chunks)} chunks", extra={"document_id": str(document_id)})
            embeddings = await self.embedding_generator.generate(chunks)

            # Step 4: Index in vector store
            await self.processing_service.update_progress(document_id, organization_id, "vector_indexing", 80)
            collection_name = f"org_{organization_id}"
            app_logger.info(f"Indexing in vector store", extra={
                "document_id": str(document_id),
                "collection": collection_name,
                "chunk_count": len(chunks)
            })
            await self.vector_indexer.index(
                collection_name=collection_name,
                chunks=chunks,
                embeddings=embeddings,
                document_id=document_id,
                organization_id=organization_id,
            )

            # Step 5: Complete processing
            await self.processing_service.update_progress(document_id, organization_id, "completed", 100)
            await self.processing_service.complete_processing(
                document_id=document_id,
                organization_id=organization_id,
                chunk_count=len(chunks),
                vector_collection=collection_name,
                text_content=text,
                page_count=page_count,
                char_count=char_count,
                extraction_method=extraction_method,
            )

            # Update document status in main table
            await self.doc_repo.update_status(
                document_id=document_id,
                organization_id=organization_id,
                status=DocumentStatus.PROCESSED,
                chunk_count=len(chunks),
                vector_collection=collection_name
            )

            app_logger.info(f"Document processing completed successfully", extra={
                "document_id": str(document_id),
                "chunk_count": len(chunks),
                "char_count": char_count
            })

            return {
                "success": True,
                "document_id": str(document_id),
                "chunk_count": len(chunks),
                "char_count": char_count,
                "collection": collection_name,
                "text_length": len(text),
            }

        except Exception as e:
            app_logger.error(f"Document processing failed", extra={
                "document_id": str(document_id),
                "error": str(e)
            })
            await self.processing_service.fail_processing(document_id, organization_id, str(e))
            await self.doc_repo.update_status(
                document_id=document_id,
                organization_id=organization_id,
                status=DocumentStatus.FAILED,
                error_message=str(e)
            )
            return {
                "success": False,
                "document_id": str(document_id),
                "error": str(e),
            }


async def process_document_background(document_id: UUID, organization_id: UUID):
    """Background task to process a document - can be called from a worker.
    Uses explicit transaction management: BEGIN -> processing -> COMMIT/ROLLBACK
    """
    from app.shared.database.session import async_session_maker
    from app.shared.database.transaction import UnitOfWork

    async with async_session_maker() as session:
        uow = UnitOfWork(session)
        async with uow:
            pipeline = DocumentProcessingPipeline(session)
            return await pipeline.process_document(document_id, organization_id)
        # Transaction committed automatically on success