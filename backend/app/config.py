"""
NeurOS 2.0 Configuration

Environment-based configuration using pydantic-settings.
Supports development, testing, and production environments.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Priority: .env file < environment variables
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like gemini_api_key
    )
    
    # Application
    APP_NAME: str = "NeurOS 2.0"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, testing, production
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database (PostgreSQL or SQLite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./neuros.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False  # Log SQL queries
    
    # Redis (for Celery and caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # SRS Configuration
    SRS_DEFAULT_EASE_FACTOR: float = 2.5
    SRS_MINIMUM_EASE_FACTOR: float = 1.3
    SRS_INITIAL_INTERVAL_DAYS: int = 1
    
    # Decay Configuration
    DECAY_HALF_LIFE_DAYS: float = 7.0  # Days until decay score halves
    DECAY_CRITICAL_THRESHOLD: int = 40  # Below this = critical decay
    DECAY_WARNING_THRESHOLD: int = 60  # Below this = warning
    
    # AI/Embeddings (optional)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    @property
    def async_database_url(self) -> str:
        """Ensure URL uses async driver."""
        url = self.DATABASE_URL
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    
    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic migrations."""
        url = self.DATABASE_URL
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "")
        return url


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
