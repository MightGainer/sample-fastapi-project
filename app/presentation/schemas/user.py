from pydantic import BaseModel

from app.infrastructure.models.user import UserEntity
from app.infrastructure.security.password_manager import IPasswordManager


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str

    def to_entity(self, password_manager: IPasswordManager) -> UserEntity:
        return UserEntity(
            email=self.email,
            password=self.password,
            username=self.username,
            is_active=True,
            is_superuser=False,
            password_manager=password_manager,
        )


class UserUpdate(UserBase):
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True
