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
    
    APP_NAME: str = "Thinking OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    DATABASE_URL: str = "sqlite:///./thinking_os.db"
    
    API_SECRET_KEY: str = "thinking-os-local-key-change-in-prod"
    
    SIMILARITY_THRESHOLD: float = 0.3
    BLOCKER_REPEAT_THRESHOLD: int = 3
    REVISION_WINDOW_DAYS: int = 7
    
    GEMINI_API_KEY: Optional[str] = None
    
    EMBEDDING_MODEL: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
