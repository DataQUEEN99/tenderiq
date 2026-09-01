#!/usr/bin/env python
"""
CLI Bootstrap Script for TenderIQ

Usage:
    python -m scripts.bootstrap --org "Acme Corp" --email admin@acme.com --password secret
    python -m scripts.bootstrap --org "Acme Corp" --email admin@acme.com --password secret --slug acme-corp

Environment variables (alternative to CLI args):
    BOOTSTRAP_ORG_NAME
    BOOTSTRAP_ADMIN_EMAIL
    BOOTSTRAP_ADMIN_PASSWORD
    BOOTSTRAP_ADMIN_FULL_NAME
    BOOTSTRAP_ORG_SLUG
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.modules.authentication.service import AuthService
from app.modules.authentication.schemas import BootstrapRequest
from app.shared.database.session import Base


async def run_bootstrap(
    org_name: str,
    admin_email: str,
    admin_password: str,
    admin_full_name: str,
    org_slug: str = None,
    database_url: str = None,
):
    """Run the bootstrap process."""
    settings = get_settings()

    # Use provided database URL or default from settings
    db_url = database_url or settings.database_url

    # Create async engine and session
    engine = create_async_engine(db_url, echo=settings.database_echo)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # Ensure tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create bootstrap request
        request = BootstrapRequest(
            organization_name=org_name,
            organization_slug=org_slug,
            admin_email=admin_email,
            admin_password=admin_password,
            admin_full_name=admin_full_name,
        )

        # Run bootstrap
        service = AuthService(session)
        try:
            result = await service.bootstrap(request)
            print(f"\n✅ Bootstrap successful!")
            print(f"   Organization: {org_name} ({result.organization_id})")
            print(f"   Admin User: {admin_email} ({result.user_id})")
            print(f"   Access Token: {result.access_token[:50]}...")
            return result
        except Exception as e:
            print(f"\n❌ Bootstrap failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Bootstrap TenderIQ with first organization and admin user")

    # CLI arguments (override env vars)
    parser.add_argument("--org", "--organization", dest="org_name",
                        default=os.getenv("BOOTSTRAP_ORG_NAME"),
                        help="Organization name (required)")
    parser.add_argument("--email", "--admin-email", dest="admin_email",
                        default=os.getenv("BOOTSTRAP_ADMIN_EMAIL"),
                        help="Admin email (required)")
    parser.add_argument("--password", "--admin-password", dest="admin_password",
                        default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
                        help="Admin password (required, min 8 chars)")
    parser.add_argument("--name", "--admin-name", dest="admin_full_name",
                        default=os.getenv("BOOTSTRAP_ADMIN_FULL_NAME", "System Administrator"),
                        help="Admin full name (default: System Administrator)")
    parser.add_argument("--slug", "--org-slug", dest="org_slug",
                        default=os.getenv("BOOTSTRAP_ORG_SLUG"),
                        help="Organization slug (auto-generated if not provided)")
    parser.add_argument("--database-url", dest="database_url",
                        default=os.getenv("DATABASE_URL"),
                        help="Database URL (default: from config)")

    args = parser.parse_args()

    # Validate required arguments
    missing = []
    if not args.org_name:
        missing.append("--org (or BOOTSTRAP_ORG_NAME)")
    if not args.admin_email:
        missing.append("--email (or BOOTSTRAP_ADMIN_EMAIL)")
    if not args.admin_password:
        missing.append("--password (or BOOTSTRAP_ADMIN_PASSWORD)")

    if missing:
        parser.error(f"Missing required arguments: {', '.join(missing)}")

    if len(args.admin_password) < 8:
        parser.error("Password must be at least 8 characters")

    # Run bootstrap
    try:
        asyncio.run(run_bootstrap(
            org_name=args.org_name,
            admin_email=args.admin_email,
            admin_password=args.admin_password,
            admin_full_name=args.admin_full_name,
            org_slug=args.org_slug,
            database_url=args.database_url,
        ))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()