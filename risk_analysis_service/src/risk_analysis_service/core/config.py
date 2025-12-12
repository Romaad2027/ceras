import os
from functools import lru_cache


class Settings:
    """Application configuration loaded from environment variables."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_SUPER_SECRET_KEY")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    TOKEN_URL: str = os.getenv("TOKEN_URL", "/api/v1/auth/login")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
