"""
NeurOS 2.0 Pattern Template Model

Code templates for patterns, used in flash-coding practice.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer, 
    String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.pattern import Pattern


class ProgrammingLanguage(str, enum.Enum):
    """Supported programming languages for templates."""
    PYTHON = "python"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"


class PatternTemplate(Base):
    """
    Code template for a thinking pattern.
    
    PURPOSE:
    Allow flash-coding practice by storing canonical
    implementations of patterns that users can:
    1. View as reference
    2. Practice writing from memory
    3. Compare their solutions against
    
    FLASH-CODING FLOW:
    1. Show pattern name + when_to_use
    2. User writes code from memory
    3. Compare with template_code
    4. Rate difficulty (feeds into SRS)
    """
    __tablename__ = "pattern_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pattern_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patterns.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Language and code
    language: Mapped[ProgrammingLanguage] = mapped_column(
        Enum(ProgrammingLanguage),
        default=ProgrammingLanguage.PYTHON,
    )
    template_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The canonical code implementation",
    )
    
    # Context for practice
    when_to_use: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Problem indicators for this pattern",
    )
    example_problem: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Example problem description",
    )
    
    # Complexity analysis
    time_complexity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Big O time complexity",
    )
    space_complexity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Big O space complexity",
    )
    
    # Practice hints
    key_insight: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="The key insight to remember",
    )
    common_mistakes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Common mistakes when implementing",
    )
    
    # Difficulty for SRS
    difficulty_rating: Mapped[int] = mapped_column(
        Integer,
        default=50,
        comment="Difficulty 1-100 for SRS calculations",
    )
    
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
    pattern: Mapped["Pattern"] = relationship("Pattern", back_populates="templates")
    
    def __repr__(self) -> str:
        return (
            f"<PatternTemplate(id={self.id}, pattern_id={self.pattern_id}, "
            f"language={self.language})>"
        )
