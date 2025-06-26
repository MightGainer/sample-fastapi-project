import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.infrastructure.db.db_context import DbContext
from app.infrastructure.db.isolation_level import IsolationLevel


class DbContextFactory:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    @asynccontextmanager
    async def create_db_context(
        self, isolation_level=IsolationLevel.READ_COMMITTED, autosave: bool = False
    ) -> AsyncGenerator[DbContext, None]:
        logging.info(f"STANDARD SESSION CREATED. Isolation level: {isolation_level.value}")

        new_engine = self.engine.execution_options(isolation_level=isolation_level.value)

        async_session_maker = async_sessionmaker(bind=new_engine, expire_on_commit=False, autocommit=False)
        async_session = async_session_maker()
        db_context = DbContext(async_session, autosave=autosave)
        try:
            await db_context.__aenter__()
            yield db_context
        except Exception as ex:
            await db_context.__aexit__(type(ex), ex, ex.__traceback__)
            raise
        else:
            await db_context.__aexit__(None, None, None)
