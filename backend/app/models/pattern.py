"""
NeurOS 2.0 Pattern Model

User-defined thinking patterns that emerge from reflection.
These patterns form your personal problem-solving vocabulary.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, 
    String, Table, Text, Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.entry import Entry
    from app.models.pattern_template import PatternTemplate


# Many-to-many association table for Entry <-> Pattern
entry_patterns = Table(
    "entry_patterns",
    Base.metadata,
    Column("entry_id", Integer, ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True),
    Column("pattern_id", Integer, ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


class Pattern(Base):
    """
    User-defined thinking pattern.
    
    PHILOSOPHY:
    Patterns are the vocabulary of your thinking process.
    They emerge from reflection and become reusable mental models.
    
    CROSS-DOMAIN VALUE:
    A pattern like "reduce to known problem" applies to:
    - DSA: Reduce unknown problem to a known algorithm
    - Debug: Reduce complex bug to simpler reproduction
    - System Design: Reduce complex system to known architectures
    
    The best patterns are domain-agnostic.
    """
    __tablename__ = "patterns"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Core identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Pattern name in YOUR words",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed explanation of the pattern",
    )
    
    # Categorization
    domain: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Primary domain (null = cross-domain)",
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # When to use / When not to use
    when_to_use: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Situations where this pattern applies",
    )
    common_triggers: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Signals that indicate this pattern might help",
    )
    common_mistakes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mistakes to avoid when applying this pattern",
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
    user: Mapped["User"] = relationship("User", back_populates="patterns")
    entries: Mapped[list["Entry"]] = relationship(
        "Entry",
        secondary=entry_patterns,
        back_populates="patterns",
    )
    templates: Mapped[list["PatternTemplate"]] = relationship(
        "PatternTemplate",
        back_populates="pattern",
        cascade="all, delete-orphan",
    )
    
    @property
    def success_rate(self) -> float | None:
        """Calculate success rate as percentage."""
        if self.usage_count == 0:
            return None
        return (self.success_count / self.usage_count) * 100
    
    @property
    def is_cross_domain(self) -> bool:
        """Check if pattern is used across multiple domains."""
        if not self.entries:
            return False
        domains = {e.entry_type for e in self.entries}
        return len(domains) > 1
    
    def __repr__(self) -> str:
        return f"<Pattern(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"
