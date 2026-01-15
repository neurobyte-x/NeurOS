"""
NeurOS 2.0 SRS Review Model

Spaced Repetition System scheduling and tracking.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, 
    Integer, String, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.config import settings

if TYPE_CHECKING:
    from app.models.user import User


class ReviewItemType(str, enum.Enum):
    """Types of items that can be reviewed."""
    ENTRY = "entry"
    PATTERN = "pattern"
    FLASHCARD = "flashcard"
    KNOWLEDGE_NODE = "knowledge_node"


class ReviewStatus(str, enum.Enum):
    """Current status of a review item."""
    LEARNING = "learning"      # Initial learning phase
    REVIEW = "review"          # Graduated to review phase
    SUSPENDED = "suspended"    # Temporarily paused
    BURIED = "buried"          # Hidden until next day


class SRSReview(Base):
    """
    SRS review scheduling record.
    
    Tracks the spaced repetition state for each reviewable item.
    Uses SuperMemo-2 algorithm for scheduling.
    
    LIFECYCLE:
    1. New item -> LEARNING status with short intervals
    2. Good reviews -> REVIEW status with increasing intervals
    3. Lapse -> Back to LEARNING with reduced ease factor
    """
    __tablename__ = "srs_reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Polymorphic reference to reviewable item
    item_type: Mapped[ReviewItemType] = mapped_column(
        Enum(ReviewItemType),
        nullable=False,
    )
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # SRS algorithm state
    interval_days: Mapped[int] = mapped_column(
        Integer,
        default=settings.SRS_INITIAL_INTERVAL_DAYS,
    )
    ease_factor: Mapped[float] = mapped_column(
        Float,
        default=settings.SRS_DEFAULT_EASE_FACTOR,
    )
    repetition_number: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status and scheduling
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus),
        default=ReviewStatus.LEARNING,
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    last_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Statistics
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    lapse_count: Mapped[int] = mapped_column(Integer, default=0)
    total_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last review quality (0-5)
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Flags
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_leech: Mapped[bool] = mapped_column(Boolean, default=False)  # Too many lapses
    
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
    user: Mapped["User"] = relationship("User", back_populates="srs_reviews")
    
    @property
    def is_due(self) -> bool:
        """Check if review is due now."""
        return datetime.now(timezone.utc) >= self.next_review_at
    
    @property
    def is_overdue(self) -> bool:
        """Check if review is overdue by more than a day."""
        if self.next_review_at is None:
            return False
        delta = datetime.now(timezone.utc) - self.next_review_at
        return delta.days >= 1
    
    @property
    def is_graduated(self) -> bool:
        """Check if item has graduated from learning phase."""
        return self.status == ReviewStatus.REVIEW
    
    def __repr__(self) -> str:
        return (
            f"<SRSReview(id={self.id}, item_type={self.item_type}, "
            f"interval={self.interval_days}d, ease={self.ease_factor:.2f})>"
        )


# Create index for efficient due review queries
from sqlalchemy import Index
Index(
    "ix_srs_reviews_user_due",
    SRSReview.user_id,
    SRSReview.next_review_at,
    SRSReview.is_suspended,
)
