import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.session import Base, engine
# Import all models
from app.modules.authentication.models import User
from app.modules.organization.models import Organization
from app.modules.document.models import Document
from app.modules.tender.models import Tender, TenderDocument, TenderSummary, EligibilityAnalysis
from app.modules.proposal.models import Proposal, ProposalSection, ProposalDocument, ComplianceMatrix
from app.modules.chat.models import ChatSession, ChatMessage
from app.modules.export.models import Export
from app.modules.company.models import CompanyProfile, CompanyDocument
from app.modules.audit.models import AuditLog

async def main():
    async with engine.begin() as conn:
        print("Ensuring all tables exist via SQLAlchemy metadata...")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables successfully verified/created!")

if __name__ == "__main__":
    asyncio.run(main())
