from pydantic_settings import BaseSettings
from os import getenv


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "secure_dev_password")
DB_HOST = getenv("DB_HOST", "db")  # Use 'db' as default for Docker
DB_NAME = getenv("DB_NAME", "dockert")
DB_PORT = int(getenv("DB_PORT", "5432"))

settings = Settings(
    POSTGRES_USER=DB_USER,
    POSTGRES_PASSWORD=DB_PASSWORD,
    POSTGRES_DB=DB_NAME,
    POSTGRES_HOST=DB_HOST,
    POSTGRES_PORT=DB_PORT
)
