from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.security.password_manager import IPasswordManager

from .base import Base


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def __init__(
            self, 
            username: str, 
            email: str, 
            password: str,
            password_manager: IPasswordManager,
            is_active: bool = True, 
            is_superuser: bool=False,
        ) -> None:
        super().__init__()
        self.username = username
        self.email = email
        self.is_active = is_active
        self.is_superuser = is_superuser
        self.password_manager = password_manager
        self.hashed_password = self.password_manager.hash_password(password=password)
