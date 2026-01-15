"""
NeurOS 2.0 Entry Model

The core unit of learning - represents a single learning moment.
"""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, 
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reflection import Reflection
    from app.models.pattern import Pattern


class EntryType(str, enum.Enum):
    """
    Domain categories for learning entries.
    
    Categories allow for domain-specific insights while
    enabling cross-domain pattern discovery.
    """
    DSA = "dsa"              # Data Structures & Algorithms
    BACKEND = "backend"      # Backend development, APIs
    AI_ML = "ai_ml"          # Machine Learning, AI, GenAI
    DEBUG = "debug"          # Debugging sessions
    INTERVIEW = "interview"  # Interview prep, mock sessions
    CONCEPT = "concept"      # Pure theory, concept learning
    PROJECT = "project"      # Project-based learning
    SYSTEM_DESIGN = "system_design"  # System design problems


class DifficultyLevel(str, enum.Enum):
    """Difficulty ratings for entries."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Entry(Base):
    """
    Core learning entry model.
    
    Represents a single learning moment across any domain.
    An entry is incomplete until it has an associated Reflection.
    
    DESIGN PHILOSOPHY:
    - Title for quick identification
    - Type for categorization and filtering
    - Tags for flexible organization
    - Difficulty for decay calculations
    - Completion requires reflection (enforced in service layer)
    """
    __tablename__ = "entries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    entry_type: Mapped[EntryType] = mapped_column(
        Enum(EntryType), 
        default=EntryType.CONCEPT,
        nullable=False,
    )
    problem_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tags for flexible categorization
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)),
        default=list,
        server_default="{}",
    )
    
    # Difficulty and time tracking
    difficulty: Mapped[DifficultyLevel | None] = mapped_column(
        Enum(DifficultyLevel),
        nullable=True,
    )
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Completion status (requires reflection)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # AI-related fields
    embedding: Mapped[list[float] | None] = mapped_column(
        ARRAY(Float),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="entries")
    reflection: Mapped[Optional["Reflection"]] = relationship(
        "Reflection",
        back_populates="entry",
        uselist=False,
        cascade="all, delete-orphan",
    )
    patterns: Mapped[list["Pattern"]] = relationship(
        "Pattern",
        secondary="entry_patterns",
        back_populates="entries",
    )
    
    def __repr__(self) -> str:
        return f"<Entry(id={self.id}, title='{self.title[:30]}...', type={self.entry_type})>"
    
    @property
    def difficulty_score(self) -> int:
        """Convert difficulty to numeric score for decay calculations."""
        mapping = {
            DifficultyLevel.EASY: 25,
            DifficultyLevel.MEDIUM: 50,
            DifficultyLevel.HARD: 75,
            DifficultyLevel.EXPERT: 100,
        }
        return mapping.get(self.difficulty, 50)
