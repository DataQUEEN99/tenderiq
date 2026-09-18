from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.shared.logging.logger import app_logger


class TransactionManager:
    """Manages database transactions with explicit commit/rollback boundaries.

    This is a lightweight wrapper around SQLAlchemy's session transaction.
    UnitOfWork is the primary transaction owner.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def begin(self) -> None:
        """Begin a new transaction if not already in one"""
        if self.session.in_transaction():
            raise RuntimeError("Transaction already in progress")
        await self.session.begin()

    async def commit(self) -> None:
        """Explicitly commit the current transaction"""
        if not self.session.in_transaction():
            raise RuntimeError("No active transaction to commit")
        await self.session.commit()

    async def rollback(self) -> None:
        """Explicitly rollback the current transaction"""
        if not self.session.in_transaction():
            raise RuntimeError("No active transaction to rollback")
        await self.session.rollback()

    @property
    def is_active(self) -> bool:
        return self.session.in_transaction()


class UnitOfWork:
    """Unit of Work pattern implementation for managing transactions across multiple repositories.

    This is the SINGLE transaction owner. It manages the transaction lifecycle:
    BEGIN → DB operations → success: COMMIT / error: ROLLBACK
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._committed = False
        self._entered = False

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator['UnitOfWork', None]:
        """Begin a new unit of work - the sole transaction boundary"""
        if self._entered:
            raise RuntimeError("UnitOfWork already entered - cannot nest transactions")
        self._entered = True
        self._committed = False

        if not self.session.in_transaction():
            async with self.session.begin():
                try:
                    yield self
                    self._committed = True
                except Exception:
                    self._committed = False
                    raise
                finally:
                    self._entered = False
        else:
            try:
                yield self
                if not self._committed:
                    await self.session.commit()
                    self._committed = True
            except Exception:
                await self.session.rollback()
                self._committed = False
                raise
            finally:
                self._entered = False

    async def commit(self) -> None:
        """Commit the unit of work"""
        if not self._committed and self.session.in_transaction():
            await self.session.commit()
            self._committed = True

    async def rollback(self) -> None:
        """Rollback the unit of work"""
        if self.session.in_transaction():
            await self.session.rollback()
            self._committed = True

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def is_active(self) -> bool:
        return self._entered and self.session.in_transaction()


@asynccontextmanager
async def get_transaction(session: AsyncSession) -> AsyncGenerator[TransactionManager, None]:
    """Get a transaction manager for the session.

    Use this for lower-level transaction control when UnitOfWork is not needed.
    """
    manager = TransactionManager(session)
    if not session.in_transaction():
        await manager.begin()
    try:
        yield manager
        if manager.is_active:
            await manager.commit()
    except Exception:
        if manager.is_active:
            await manager.rollback()
        raise