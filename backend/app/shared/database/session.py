from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings
from app.shared.database.transaction import UnitOfWork

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Get a raw database session without transaction management.
    Use for operations that manage their own transactions (e.g., migrations)."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """Get a database session with automatic transaction management.
    Commits on success, rolls back on exception."""
    async with async_session_maker() as session:
        uow = UnitOfWork(session)
        async with uow:
            try:
                yield session
                # Commit happens automatically in UnitOfWork.__aexit__ on success
            except Exception:
                # Rollback happens automatically in UnitOfWork.__aexit__ on exception
                raise


# Note: Database initialization is now handled by alembic migrations.
# Use `python -m alembic upgrade head` or the run_migrations.py script.
# The init_db() function that used create_all() has been removed.