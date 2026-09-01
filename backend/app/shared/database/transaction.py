from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.shared.logging.logger import app_logger


class TransactionManager:
    """Manages database transactions with explicit commit/rollback boundaries"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for explicit transaction handling"""
        try:
            # Begin transaction
            self._transaction = self.session.begin()
            await self._transaction.__aenter__()

            yield self.session

            # Commit transaction
            await self._transaction.__aexit__(None, None, None)
            self._transaction = None

        except SQLAlchemyError as e:
            # Rollback on error
            if self._transaction:
                await self._transaction.__aexit__(type(e), e, e.__traceback__)
                self._transaction = None
            app_logger.error(f"Transaction rolled back due to error", extra={"error": str(e)})
            raise
        except Exception as e:
            # Rollback on any exception
            if self._transaction:
                await self._transaction.__aexit__(type(e), e, e.__traceback__)
                self._transaction = None
            app_logger.error(f"Transaction rolled back due to exception", extra={"error": str(e)})
            raise

    async def commit(self) -> None:
        """Explicitly commit the current transaction"""
        if self._transaction:
            await self._transaction.__aexit__(None, None, None)
            self._transaction = None

    async def rollback(self) -> None:
        """Explicitly rollback the current transaction"""
        if self._transaction:
            await self._transaction.__aexit__(Exception("Manual rollback"), None, None)
            self._transaction = None


@asynccontextmanager
async def get_transaction(session: AsyncSession) -> AsyncGenerator[TransactionManager, None]:
    """Get a transaction manager for the session"""
    manager = TransactionManager(session)
    try:
        yield manager
    finally:
        # Ensure any pending transaction is rolled back
        if manager._transaction:
            await manager.rollback()


class UnitOfWork:
    """Unit of Work pattern implementation for managing transactions across multiple repositories"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._tx_manager = TransactionManager(session)
        self._committed = False

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator['UnitOfWork', None]:
        """Begin a new unit of work"""
        async with self._tx_manager.transaction() as session:
            self.session = session
            try:
                yield self
                await self._tx_manager.commit()
                self._committed = True
            except Exception:
                await self._tx_manager.rollback()
                self._committed = False
                raise

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