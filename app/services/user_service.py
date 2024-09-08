from app.models.user import UserEntity
from app.db.db_context import DbContext


class UserService:
    def __init__(self):
        pass

    async def create_user(self, user: UserEntity, db_context: DbContext) -> UserEntity:
        await db_context.users.add(user)
        await db_context.save_changes()
        return user

    async def get_user(self, user_id: int, db_context: DbContext) -> UserEntity | None:
        return await db_context.users.get(user_id)

    async def get_all_users(self, db_context: DbContext) -> list[UserEntity]:
        return await db_context.users.all()
