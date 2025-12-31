"""
Configuration module for Thinking OS.

WHY: Centralized configuration allows easy environment switching
and keeps sensitive data/paths in one place. Future-proofed for
multi-environment deployment and external config sources.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with sensible defaults for single-user mode.
    
    WHY: Using Pydantic BaseSettings enables:
    - Type validation at startup
    - Environment variable override
    - Clear documentation of all config options
    """
    
    # Application
    APP_NAME: str = "Thinking OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    # WHY: SQLite for simplicity, but path is configurable for testing/migration
    DATABASE_URL: str = "sqlite:///./thinking_os.db"
    
    # Single-user auth (simple token for API access)
    # WHY: No complex auth needed for personal system, but hook exists for future
    API_SECRET_KEY: str = "thinking-os-local-key-change-in-prod"
    
    # Recall system settings
    # WHY: These thresholds tune the intelligence layer sensitivity
    SIMILARITY_THRESHOLD: float = 0.3  # For future embedding-based search
    BLOCKER_REPEAT_THRESHOLD: int = 3   # Times before flagging repeated blocker
    REVISION_WINDOW_DAYS: int = 7       # Days to look back for revision suggestions
    
    # Gemini AI settings
    GEMINI_API_KEY: Optional[str] = None  # Required for AI-assisted entry creation
    
    # Future: Embedding/LLM hooks
    EMBEDDING_MODEL: Optional[str] = None  # e.g., "text-embedding-ada-002"
    LLM_MODEL: Optional[str] = None        # e.g., "gpt-4"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings instance
settings = Settings()

# Ensure data directory exists
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
