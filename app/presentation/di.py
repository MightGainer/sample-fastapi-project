from typing import Callable, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.infrastructure.db.db_context_factory import DbContextFactory
from app.infrastructure.dependencies.service_collection import ServiceCollection
from app.infrastructure.security.password_manager import (
    IPasswordManager,
    PasswordManager,
)
from app.infrastructure.services.user_service import IUserService, UserService
from app.presentation.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)

# DI setup
services = ServiceCollection()
services.add_singleton(AsyncEngine, engine)
services.add_singleton(DbContextFactory, DbContextFactory)
services.add_transient(IUserService, UserService)
services.add_transient(IPasswordManager, PasswordManager)

service_provider = services.build_service_provider()


def resolve(dependency: Type[object]) -> Callable[..., object]:
    async def _resolver() -> object:
        return await service_provider.get_service(dependency)

    return Depends(_resolver)  # type: ignore
