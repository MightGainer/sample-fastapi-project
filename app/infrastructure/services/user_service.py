from abc import ABC, abstractmethod
from typing import Self, Sequence

from app.infrastructure.db.db_context import DbContext
from app.infrastructure.models.user import UserEntity


class IUserService(ABC):
    @abstractmethod
    async def create_user(self: Self, user: UserEntity, db_context: DbContext) -> UserEntity: ...

    @abstractmethod
    async def get_user(self: Self, user_id: int, db_context: DbContext) -> UserEntity | None: ...

    @abstractmethod
    async def get_all_users(self: Self, db_context: DbContext) -> Sequence[UserEntity]: ...


class UserService(IUserService):
    def __init__(self):
        pass

    async def create_user(self, user: UserEntity, db_context: DbContext) -> UserEntity:
        await db_context.users.add(user)
        await db_context.save()
        return user

    async def get_user(self, user_id: int, db_context: DbContext) -> UserEntity | None:
        return await db_context.users.get(user_id)

    async def get_all_users(self, db_context: DbContext) -> Sequence[UserEntity]:
        return await db_context.users.all()
