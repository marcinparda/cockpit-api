from typing import cast
from pydantic_settings import BaseSettings
from os import getenv
from typing import List, Union, Literal
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_DAYS: int = 30  # Refresh token expires in 30 days

    # Token Management Settings
    TOKEN_CLEANUP_ENABLED: bool = True
    TOKEN_CLEANUP_INTERVAL_HOURS: int = 24
    TOKEN_CLEANUP_RETENTION_DAYS: int = 7
    TOKEN_CLEANUP_BATCH_SIZE: int = 1000
    TOKEN_CLEANUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM UTC

    # Password Hashing Settings
    BCRYPT_ROUNDS: int = 12

    # Cookie Settings
    COOKIE_DOMAIN: str = "localhost"  # Will be overridden by environment
    COOKIE_SECURE: bool = False  # Will be overridden by environment
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: Literal["strict", "lax", "none"] = "strict"
    ACCESS_TOKEN_COOKIE_MAX_AGE: int = 1800  # 30 minutes
    REFRESH_TOKEN_COOKIE_MAX_AGE: int = 604800  # 7 days

    # Environment Detection
    ENVIRONMENT: str = "development"  # production, development, test

    # CORS Settings
    CORS_ORIGINS: Union[List[AnyHttpUrl], List[str], str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
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

# JWT settings from environment
JWT_SECRET_KEY = getenv(
    "JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
JWT_ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(getenv("JWT_EXPIRE_HOURS", "24"))
BCRYPT_ROUNDS = int(getenv("BCRYPT_ROUNDS", "12"))

# Cookie settings from environment
COOKIE_DOMAIN = getenv("COOKIE_DOMAIN", "localhost")
COOKIE_SECURE = getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE_STR = getenv("COOKIE_SAMESITE", "strict")
ENVIRONMENT = getenv("ENVIRONMENT", "development")

# Validate and cast COOKIE_SAMESITE value
if COOKIE_SAMESITE_STR in ["strict", "lax", "none"]:
    COOKIE_SAMESITE = cast(
        Literal["strict", "lax", "none"], COOKIE_SAMESITE_STR)
else:
    COOKIE_SAMESITE = "strict"

# CORS settings from environment
CORS_ORIGINS_STR = getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:4200,http://localhost:8000,https://*.parda.me"
)
CORS_ORIGINS = CORS_ORIGINS_STR.split(",")

settings = Settings(
    POSTGRES_USER=DB_USER,
    POSTGRES_PASSWORD=DB_PASSWORD,
    POSTGRES_DB=DB_NAME,
    POSTGRES_HOST=DB_HOST,
    POSTGRES_PORT=DB_PORT,
    JWT_SECRET_KEY=JWT_SECRET_KEY,
    JWT_ALGORITHM=JWT_ALGORITHM,
    JWT_EXPIRE_HOURS=JWT_EXPIRE_HOURS,
    BCRYPT_ROUNDS=BCRYPT_ROUNDS,
    CORS_ORIGINS=CORS_ORIGINS,
    COOKIE_DOMAIN=COOKIE_DOMAIN,
    COOKIE_SECURE=COOKIE_SECURE,
    COOKIE_SAMESITE=COOKIE_SAMESITE,
    ENVIRONMENT=ENVIRONMENT
)
