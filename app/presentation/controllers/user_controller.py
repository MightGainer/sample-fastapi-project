from fastapi import APIRouter, HTTPException, Request
from fastapi_utils.cbv import cbv

from app.infrastructure.db.db_context_factory import DbContextFactory
from app.infrastructure.security.password_manager import IPasswordManager
from app.infrastructure.services.user_service import IUserService
from app.presentation.di import resolve
from app.presentation.middlewares.permissions import (
    allow_anonymous,
    require_permissions,
)
from app.presentation.schemas.user import User, UserCreate

router = APIRouter()


@cbv(router)
class UserController:
    def __init__(
        self,
        user_service: IUserService = resolve(IUserService),
        db_context_factory: DbContextFactory = resolve(DbContextFactory),
        password_manager: IPasswordManager = resolve(IPasswordManager)
    ) -> None:
        self.user_service = user_service
        self.db_context_factory = db_context_factory
        self.password_manager = password_manager

    @router.post("/users", response_model=User)
    @require_permissions(["user:create"])
    async def create_user(self, request: Request, user: UserCreate) -> User:
        async with self.db_context_factory.create_db_context() as db_context:
            user_entity = await self.user_service.create_user(user.to_entity(self.password_manager), db_context)
            return User.model_validate(user_entity)

    @router.get("/users/{user_id}", response_model=User)
    @require_permissions(["user:read"])
    async def get_user(self, request: Request, user_id: int) -> User:
        async with self.db_context_factory.create_db_context() as db_context:
            user = await self.user_service.get_user(user_id, db_context)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return User.model_validate(user)

    @router.get("/users", response_model=list[User])
    @require_permissions(["user:read"])
    async def get_all_users(self, request: Request) -> list[User]:
        async with self.db_context_factory.create_db_context() as db_context:
            users = await self.user_service.get_all_users(db_context)
            return [User.model_validate(user) for user in users]

    @router.get("/public", response_model=str)
    @allow_anonymous("/api/public")
    async def public_endpoint(self, request: Request) -> str:
        return "This is a public endpoint"
