from typing import Callable, Type
from fastapi import Depends
from app.dependencies.service_collection import ServiceCollection
from app.services.user_service import UserService
from app.db.db_context_factory import DbContextFactory
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from app.core.settings import load_settings

settings = load_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)

# Dependency Injection setup
services = ServiceCollection()
services.add_singleton(AsyncEngine, engine)
services.add_singleton(DbContextFactory, DbContextFactory)
services.add_transient(UserService, UserService)

service_provider = services.build_service_provider()


def resolve_dependency(dependency: Type[object]) -> Callable[..., object]:
    async def _resolver() -> object:
        return await service_provider.get_service(dependency)

    return Depends(_resolver)  # type: ignore
