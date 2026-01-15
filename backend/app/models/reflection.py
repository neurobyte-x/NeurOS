"""
NeurOS 2.0 Reflection Model

Mandatory reflection data for learning entries.
This is what makes NeurOS different from regular note-taking.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.entry import Entry


class Reflection(Base):
    """
    Mandatory reflection attached to every completed entry.
    
    PHILOSOPHY:
    Without reflection, there is no persistence. This model captures
    the metacognitive process - not just what you learned, but HOW
    you learned it.
    
    FIELDS EXPLAINED:
    - problem_context: What were you trying to solve/understand?
    - initial_blocker: What confused you or stopped your progress?
    - trigger_signal: What insight unlocked the solution?
    - key_pattern: Name the pattern in YOUR words (builds vocabulary)
    - mistakes_edge_cases: What to remember for next time
    """
    __tablename__ = "reflections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("entries.id", ondelete="CASCADE"),
        unique=True,  # One reflection per entry
        nullable=False,
    )
    
    # Core reflection fields (all required)
    problem_context: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What problem/concept were you working on?",
    )
    initial_blocker: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What was confusing or blocking progress?",
    )
    trigger_signal: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What insight/realization led to understanding?",
    )
    key_pattern: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Name the thinking pattern in your own words",
    )
    mistakes_edge_cases: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What mistakes to avoid or edge cases to remember?",
    )
    
    # Optional extended reflection
    what_i_would_do_differently: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="If you faced this again, what would you change?",
    )
    related_concepts: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="What other concepts does this connect to?",
    )
    confidence_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="1-5 confidence in understanding (for SRS)",
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
    
    # Relationship
    entry: Mapped["Entry"] = relationship("Entry", back_populates="reflection")
    
    def __repr__(self) -> str:
        return f"<Reflection(id={self.id}, entry_id={self.entry_id}, pattern='{self.key_pattern[:30]}...')>"
