"""
NeurOS 2.0 Decay Tracking Model

Temporal tracking for knowledge decay based on Ebbinghaus curve.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, 
    Integer, String, Date,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class TrackableType(str, enum.Enum):
    """Types of items that can be tracked for decay."""
    ENTRY = "entry"
    PATTERN = "pattern"
    CONCEPT = "concept"
    KNOWLEDGE_NODE = "knowledge_node"


class DecayTracking(Base):
    """
    Decay tracking for knowledge items.
    
    PURPOSE:
    Track when items were last practiced and calculate decay
    based on the Ebbinghaus forgetting curve. This enables:
    - Proactive decay alerts
    - Intelligent review prioritization
    - Visual decay heatmaps
    
    DECAY CALCULATION:
    decay_score = retention * 100
    Where retention follows: R = e^(-t/S)
    - t = time since last practice
    - S = stability (based on reviews and difficulty)
    """
    __tablename__ = "decay_trackings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Polymorphic reference to trackable item
    trackable_type: Mapped[TrackableType] = mapped_column(
        Enum(TrackableType),
        nullable=False,
    )
    trackable_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Current state
    decay_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
        comment="Current retention score (0-100)",
    )
    stability_factor: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        comment="Memory stability multiplier",
    )
    
    # Practice history
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    times_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Scheduling
    next_review_date: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
        comment="Recommended next review date",
    )
    
    # Item characteristics
    initial_difficulty: Mapped[int] = mapped_column(
        Integer,
        default=50,
        comment="Initial difficulty (1-100, higher = harder)",
    )
    
    # Last review quality (affects stability)
    last_quality: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Quality of last review (0-5)",
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
    user: Mapped["User"] = relationship("User", back_populates="decay_trackings")
    
    @property
    def is_critical(self) -> bool:
        """Check if decay is at critical level."""
        from app.config import settings
        return self.decay_score < settings.DECAY_CRITICAL_THRESHOLD
    
    @property
    def is_warning(self) -> bool:
        """Check if decay is at warning level."""
        from app.config import settings
        return self.decay_score < settings.DECAY_WARNING_THRESHOLD
    
    @property
    def status(self) -> str:
        """Get human-readable decay status."""
        if self.decay_score >= 80:
            return "fresh"
        elif self.decay_score >= 60:
            return "stable"
        elif self.decay_score >= 40:
            return "decaying"
        elif self.decay_score >= 20:
            return "critical"
        else:
            return "forgotten"
    
    def __repr__(self) -> str:
        return (
            f"<DecayTracking(id={self.id}, type={self.trackable_type}, "
            f"score={self.decay_score}, status={self.status})>"
        )


# Create indexes for efficient queries
from sqlalchemy import Index
Index(
    "ix_decay_tracking_user_score",
    DecayTracking.user_id,
    DecayTracking.decay_score,
)
Index(
    "ix_decay_tracking_next_review",
    DecayTracking.user_id,
    DecayTracking.next_review_date,
)
