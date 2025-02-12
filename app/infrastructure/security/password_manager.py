from abc import ABC, abstractmethod
from typing import Self

import bcrypt


class IPasswordManager(ABC):
    @abstractmethod
    def hash_password(self: Self, password: str) -> str: ...

    @abstractmethod
    def verify_password(self: Self, plain_password: str, hashed_password: bytes) -> bool: ...


class PasswordManager(IPasswordManager):
    def hash_password(self, password: str) -> str:
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
        return str(hashed_password)

    def verify_password(self, plain_password: str, hashed_password: bytes) -> bool:
        password_byte_enc = plain_password.encode("utf-8")
        return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)
