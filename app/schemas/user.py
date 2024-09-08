from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

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
