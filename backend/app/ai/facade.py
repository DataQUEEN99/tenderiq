from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.ai.ingestion.text_extractor import TextExtractor
from app.ai.ingestion.chunker import Chunker
from app.ai.ingestion.embedding_generator import EmbeddingGenerator
from app.ai.ingestion.vector_indexer import VectorIndexer
from app.ai.retrieval.retriever import Retriever
from app.ai.generation.summary import SummaryGenerator
from app.ai.generation.eligibility import EligibilityAnalyzer
from app.ai.generation.compliance import ComplianceChecker
from app.ai.generation.proposal import ProposalGenerator
from app.ai.generation.chat import ChatEngine
from app.config import get_settings


class AIFacade:
    def __init__(self):
        self.settings = get_settings()
        self.text_extractor = TextExtractor()
        self.chunker = Chunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_indexer = VectorIndexer()
        self.retriever = Retriever()
        self.summary_generator = SummaryGenerator()
        self.eligibility_analyzer = EligibilityAnalyzer()
        self.compliance_checker = ComplianceChecker()
        self.proposal_generator = ProposalGenerator()
        self.chat_engine = ChatEngine()

    async def process_document(self, organization_id: UUID, document_id: UUID, file_path: str, mime_type: str) -> Dict[str, Any]:
        text = await self.text_extractor.extract(file_path, mime_type)
        chunks = self.chunker.chunk(text)
        embeddings = await self.embedding_generator.generate(chunks)
        collection = f"org_{organization_id}"
        await self.vector_indexer.index(collection, chunks, embeddings, document_id, organization_id)
        return {
            "chunk_count": len(chunks),
            "collection": collection,
            "text_length": len(text)
        }

    async def search_documents(self, organization_id: UUID, query: str,
                               document_type: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        collection = f"org_{organization_id}"
        results = await self.retriever.search(collection, query, top_k, {"organization_id": str(organization_id)})
        return results

    async def generate_summary(
        self,
        organization_id: UUID,
        document_ids: List[UUID],
        summary_type: str = "executive",
        tender_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        return await self.summary_generator.generate(
            organization_id=organization_id,
            document_ids=document_ids,
            summary_type=summary_type,
            tender_id=tender_id,
            user_id=user_id,
            db=db,
        )

    async def analyze_eligibility(
        self,
        organization_id: UUID,
        tender_id: UUID,
        company_profile: Dict[str, Any],
        company_profile_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        return await self.eligibility_analyzer.analyze(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile=company_profile,
            company_profile_id=company_profile_id,
            user_id=user_id,
            db=db,
        )

    async def check_compliance(
        self,
        organization_id: UUID,
        tender_id: UUID,
        proposal_id: UUID,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        return await self.compliance_checker.check(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            user_id=user_id,
            db=db,
        )

    async def generate_proposal(self, organization_id: UUID, tender_id: UUID, company_profile: Dict[str, Any],
                                requirements: List[str]) -> Dict[str, Any]:
        return await self.proposal_generator.generate(organization_id, tender_id, company_profile, requirements)

    async def chat(self, organization_id: UUID, message: str, conversation_id: Optional[UUID] = None,
                   context_document_ids: Optional[List[UUID]] = None) -> Dict[str, Any]:
        return await self.chat_engine.chat(organization_id, message, conversation_id, context_document_ids)