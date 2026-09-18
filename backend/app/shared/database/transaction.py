from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.shared.logging.logger import app_logger


class TransactionManager:
    """Manages database transactions with explicit commit/rollback boundaries.

    This is a lightweight wrapper around SQLAlchemy's transaction.
    The UnitOfWork owns the transaction lifecycle - this class just provides
    begin/commit/rollback methods without context manager logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None
        self._active = False

    async def begin(self) -> None:
        """Begin a new transaction"""
        if self._active:
            raise RuntimeError("Transaction already in progress")
        self._transaction = self.session.begin()
        await self._transaction.__aenter__()
        self._active = True

    async def commit(self) -> None:
        """Explicitly commit the current transaction"""
        if not self._active or not self._transaction:
            raise RuntimeError("No active transaction to commit")
        await self._transaction.__aexit__(None, None, None)
        self._transaction = None
        self._active = False

    async def rollback(self) -> None:
        """Explicitly rollback the current transaction"""
        if not self._active or not self._transaction:
            raise RuntimeError("No active transaction to rollback")
        await self._transaction.__aexit__(Exception("Manual rollback"), None, None)
        self._transaction = None
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active


class UnitOfWork:
    """Unit of Work pattern implementation for managing transactions across multiple repositories.

    This is the SINGLE transaction owner. It manages the transaction lifecycle:
    BEGIN → DB operations → success: COMMIT / error: ROLLBACK
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._tx_manager = TransactionManager(session)
        self._committed = False
        self._entered = False

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator['UnitOfWork', None]:
        """Begin a new unit of work - the sole transaction boundary"""
        if self._entered:
            raise RuntimeError("UnitOfWork already entered - cannot nest transactions")
        self._entered = True
        await self._tx_manager.begin()
        try:
            yield self
            await self._tx_manager.commit()
            self._committed = True
        except Exception:
            await self._tx_manager.rollback()
            self._committed = False
            raise
        finally:
            self._entered = False

    async def commit(self) -> None:
        """Commit the unit of work"""
        if not self._committed:
            await self._tx_manager.commit()
            self._committed = True

    async def rollback(self) -> None:
        """Rollback the unit of work"""
        if not self._committed:
            await self._tx_manager.rollback()
            self._committed = True  # Mark as resolved

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def is_active(self) -> bool:
        return self._tx_manager.is_active


@asynccontextmanager
async def get_transaction(session: AsyncSession) -> AsyncGenerator[TransactionManager, None]:
    """Get a transaction manager for the session.

    Use this for lower-level transaction control when UnitOfWork is not needed.
    The caller is responsible for calling begin()/commit()/rollback().
    """
    manager = TransactionManager(session)
    try:
        yield manager
    finally:
        # Ensure any pending transaction is rolled back
        if manager.is_active:
            await manager.rollback()