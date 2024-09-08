from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

T = TypeVar("T")


class DbSet(Generic[T]):
    def __init__(
        self, entity_type: Type[T], session: AsyncSession, autosave: bool = True
    ) -> None:
        self.entity_type = entity_type
        self.session = session
        self.autosave = autosave

    async def create(self, **kwargs) -> T:
        entity = self.entity_type(**kwargs)
        return await self.add(entity)

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.__autosave_and_refresh(entity)
        return entity

    async def add_all(self, entities: list[T]) -> list[T]:
        self.session.add_all(entities)
        await self.__autosave()
        return entities

    async def get(self, entity_id: int) -> T | None:
        return await self.session.get(self.entity_type, entity_id)

    async def get_one(self, *criteria) -> T | None:
        result = await self.session.execute(select(self.entity_type).filter(*criteria))
        return result.scalars().first()

    async def all(self) -> Sequence[T]:
        result = await self.session.execute(select(self.entity_type))
        return result.scalars().all()

    async def filter(self, *criteria) -> Sequence[T]:
        result = await self.session.execute(select(self.entity_type).filter(*criteria))
        return result.scalars().all()

    async def update(self, entity: T) -> T:
        self.session.add(entity)
        await self.__autosave_and_refresh(entity)
        return entity

    async def update_all(self, entities: list[T]) -> list[T]:
        for entity in entities:
            self.session.add(entity)
        await self.__autosave()
        return entities

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.__autosave()

    async def delete_all(self, entities: list[T]) -> None:
        for entity in entities:
            await self.session.delete(entity)
        await self.__autosave()

    async def refresh(self, entity: T) -> T:
        await self.session.refresh(entity)
        return entity

    async def save(self) -> None:
        await self.session.commit()

    async def __autosave(self) -> None:
        if self.autosave:
            await self.save()

    async def __autosave_and_refresh(self, entity: T) -> None:
        if self.autosave:
            await self.save()
            await self.refresh(entity)
