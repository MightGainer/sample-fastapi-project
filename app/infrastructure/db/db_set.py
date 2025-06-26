from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import Result, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

T = TypeVar("T")


class DbSet(Generic[T]):
    def __init__(self, entity_type: Type[T], session: AsyncSession, autosave: bool = False) -> None:
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

    async def try_get(self, entity_id: int) -> T | None:
        return await self.session.get(self.entity_type, entity_id)

    async def try_get_first(self, *criteria, or_conditions: list | tuple | None = None) -> T | None:
        result = await self.__search_by_criteria(*criteria, or_conditions=or_conditions)
        return result.scalars().first()

    async def try_get_single(self, *criteria, or_conditions: list | tuple | None = None) -> T | None:
        result = await self.__search_by_criteria(*criteria, or_conditions=or_conditions)
        return result.scalars().one_or_none()

    async def all(self) -> Sequence[T]:
        result = await self.session.execute(select(self.entity_type))
        return result.scalars().all()

    async def filter(self, *criteria, or_conditions: list | tuple | None = None) -> Sequence[T]:
        result = await self.__search_by_criteria(*criteria, or_conditions=or_conditions)
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

    async def __search_by_criteria(self, *criteria, or_conditions: list | tuple | None = None) -> Result[tuple[T]]:
        and_condition = and_(*criteria)
        or_condition = or_(*or_conditions) if or_conditions else None
        if or_condition is not None:
            final_condition = and_(and_condition, or_condition)
        else:
            final_condition = and_condition

        return await self.session.execute(select(self.entity_type).filter(final_condition))

    async def __autosave(self) -> None:
        if self.autosave:
            await self.save()

    async def __autosave_and_refresh(self, entity: T) -> None:
        if self.autosave:
            await self.save()
            await self.refresh(entity)
