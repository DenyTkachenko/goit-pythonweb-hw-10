from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    API_TITLE: str = "Contacts API"
    API_VERSION: str = "2.0.0"
    DEBUG: bool = True

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    VERIFY_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = ""  # "http://localhost:3000,http://127.0.0.1:3000"

    CLOUDINARY_URL: Optional[str] = None
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

settings = Settings()
