from pydantic_settings import BaseSettings
from os import getenv
from typing import List, Union
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # CORS Settings
    CORS_ORIGINS: Union[List[AnyHttpUrl], List[str], str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "secure_dev_password")
DB_HOST = getenv("DB_HOST", "db")  # Use 'db' as default for Docker
DB_NAME = getenv("DB_NAME", "dockert")
DB_PORT = int(getenv("DB_PORT", "5432"))

# CORS settings from environment
CORS_ORIGINS = getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:4200,http://localhost:8000").split(",")

settings = Settings(
    POSTGRES_USER=DB_USER,
    POSTGRES_PASSWORD=DB_PASSWORD,
    POSTGRES_DB=DB_NAME,
    POSTGRES_HOST=DB_HOST,
    POSTGRES_PORT=DB_PORT,
    CORS_ORIGINS=CORS_ORIGINS
)
