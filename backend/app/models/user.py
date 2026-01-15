"""
NeurOS 2.0 User Model

User authentication and profile management.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.entry import Entry
    from app.models.pattern import Pattern
    from app.models.srs_review import SRSReview
    from app.models.decay_tracking import DecayTracking
    from app.models.knowledge_node import KnowledgeNode


class User(Base):
    """
    User model for authentication and profile.
    
    Relationships:
    - entries: Learning entries created by user
    - patterns: Custom thinking patterns defined by user
    - srs_reviews: SRS scheduling data
    - decay_trackings: Decay tracking records
    - knowledge_nodes: Personal knowledge graph nodes
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Settings
    daily_review_goal: Mapped[int] = mapped_column(Integer, default=10)
    preferred_study_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Relationships
    entries: Mapped[list["Entry"]] = relationship(
        "Entry", back_populates="user", cascade="all, delete-orphan"
    )
    patterns: Mapped[list["Pattern"]] = relationship(
        "Pattern", back_populates="user", cascade="all, delete-orphan"
    )
    srs_reviews: Mapped[list["SRSReview"]] = relationship(
        "SRSReview", back_populates="user", cascade="all, delete-orphan"
    )
    decay_trackings: Mapped[list["DecayTracking"]] = relationship(
        "DecayTracking", back_populates="user", cascade="all, delete-orphan"
    )
    knowledge_nodes: Mapped[list["KnowledgeNode"]] = relationship(
        "KnowledgeNode", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
