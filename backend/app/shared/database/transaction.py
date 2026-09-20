from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.logging.logger import app_logger


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing transactions.

    This is the SINGLE transaction owner. It manages the transaction lifecycle:
    BEGIN -> DB operations -> success: COMMIT / error: ROLLBACK

    Usage:
        uow = UnitOfWork(session)
        async with uow:
            # do database operations
            await repo.create(entity)
        # Transaction committed automatically on success, rolled back on exception

    Or with explicit begin:
        async with uow.begin():
            ...
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._committed = False
        self._entered = False

    async def __aenter__(self) -> 'UnitOfWork':
        """Begin a new unit of work - the sole transaction boundary."""
        if self._entered:
            raise RuntimeError("UnitOfWork already entered - cannot reuse")
        self._entered = True
        self._committed = False

        if self.session.in_transaction():
            raise RuntimeError("Session already has an active transaction - UnitOfWork must be the sole transaction owner")

        # Begin transaction
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit on success, rollback on exception."""
        try:
            if exc_type is not None:
                # Exception occurred - rollback
                if self.session.in_transaction():
                    await self.session.rollback()
                    app_logger.debug("UnitOfWork rolled back due to exception", extra={"error": str(exc_val)})
                self._committed = False
            else:
                # Success - commit
                if self.session.in_transaction():
                    await self.session.commit()
                    self._committed = True
                    app_logger.debug("UnitOfWork committed successfully")
        finally:
            self._entered = False

    async def commit(self) -> None:
        """Explicitly commit the unit of work."""
        if self._committed:
            raise RuntimeError("UnitOfWork already committed")
        if not self._entered:
            raise RuntimeError("UnitOfWork not entered - cannot commit")
        if not self.session.in_transaction():
            raise RuntimeError("No active transaction to commit")

        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Explicitly rollback the unit of work."""
        if self._committed:
            raise RuntimeError("UnitOfWork already committed - cannot rollback")
        if not self._entered:
            raise RuntimeError("UnitOfWork not entered - cannot rollback")
        if not self.session.in_transaction():
            raise RuntimeError("No active transaction to rollback")

        await self.session.rollback()
        self._committed = True  # Mark as "finalized" to prevent double rollback

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def is_active(self) -> bool:
        return self._entered and self.session.in_transaction()