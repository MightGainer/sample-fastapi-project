from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.db_set import DbSet
from app.infrastructure.models.user import UserEntity


class DbContext:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

        # entities
        self.users = DbSet(UserEntity, session)

    async def __aenter__(self) -> Self:
        self._transaction = await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self._transaction.rollback()
        await self.session.close()

    async def save(self) -> None:
        await self.session.commit()
