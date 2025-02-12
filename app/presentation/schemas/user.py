from pydantic import BaseModel

from app.infrastructure.models.user import UserEntity


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str

    def to_entity(self) -> UserEntity:
        return UserEntity(
            email=self.email,
            password=self.password,
            username=self.username,
            is_active=True,
            is_superuser=False,
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

    def __init__(self, user: UserEntity) -> None:
        self.id = user.id
        self.is_active = user.is_active
        self.is_superuser = user.is_superuser
        self.email = user.email
        self.username = user.username
