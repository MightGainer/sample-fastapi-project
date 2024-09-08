from fastapi import APIRouter, HTTPException, Request
from app.schemas.user import User, UserCreate
from app.services.user_service import UserService
from app.db.db_context_factory import DbContextFactory
from app.middlewares.permissions import require_permissions, allow_anonymous
from app.di import resolve_dependency
from fastapi_utils.cbv import cbv

router = APIRouter()

@cbv(router)
class UserController:
    def __init__(
        self,
        user_service: UserService = resolve_dependency(UserService),
        db_context_factory: DbContextFactory = resolve_dependency(DbContextFactory),
    ) -> None:
        self.user_service = user_service
        self.db_context_factory = db_context_factory

    @router.post("/users", response_model=User)
    @require_permissions(["user:create"])
    async def create_user(self, request: Request, user: UserCreate) -> User:
        async with self.db_context_factory.create_db_context() as db_context:
            user_entity = await self.user_service.create_user(user, db_context)
            return User.from_orm(user_entity)

    @router.get("/users/{user_id}", response_model=User)
    @require_permissions(["user:read"])
    async def get_user(self, request: Request, user_id: int) -> User:
        async with self.db_context_factory.create_db_context() as db_context:
            user = await self.user_service.get_user(user_id, db_context)
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return user

    @router.get("/users", response_model=list[User])
    @require_permissions(["user:read"])
    async def get_all_users(self, request: Request) -> list[User]:
        async with self.db_context_factory.create_db_context() as db_context:
            users = await self.user_service.get_all_users(db_context)
            return [User.from_orm(user) for user in users]

    @router.get("/public", response_model=str)
    @allow_anonymous("/api/public")
    async def public_endpoint(self) -> str:
        return "This is a public endpoint"
