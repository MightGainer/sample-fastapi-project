import os
import json
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = Field(default="FastAPI Sample Project")
    debug: bool = Field(default=False)
    database_url: str = Field(default="sqlite+aiosqlite:///./test.db")
    secret_key: str = Field(default="your_secret_key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)


def load_settings() -> Settings:
    env = os.getenv("ENV", "development")
    settings_file = os.path.join("config", f"{env}.appsettings.json")
    
    if os.path.exists(settings_file):
        with open(settings_file, "r") as file:
            settings_data = json.load(file)
        return Settings(**settings_data)
    
    return Settings()
