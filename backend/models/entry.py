"""
Entry model - the core unit of learning in Thinking OS.

WHY: An entry represents a single learning moment - a problem solved,
a bug fixed, an experiment run. It's domain-agnostic to capture
learning across DSA, Backend, AI/ML, Interview prep, etc.

DESIGN DECISION: Entry is incomplete without Reflection.
The relationship is enforced at the service layer to ensure
no entry exists without mandatory reflection fields.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    Enum, Boolean, Float
)
from sqlalchemy.orm import relationship

from database import Base


class EntryType(enum.Enum):
    """
    Domain categories for entries.
    
    WHY: Enum ensures consistent categorization while allowing
    cross-domain pattern discovery. Each type may have slightly
    different context requirements.
    """
    DSA = "dsa"                    # Data Structures & Algorithms / CP
    BACKEND = "backend"            # FastAPI, APIs, system design
    AI_ML = "ai_ml"                # Machine Learning, GenAI, experiments
    DEBUG = "debug"                # Bug fixes, debugging sessions
    INTERVIEW = "interview"        # Interview questions, mock sessions
    CONCEPT = "concept"            # Pure learning, theory understanding
    PROJECT = "project"            # Project-based learning


class Entry(Base):
    """
    Core learning entry.
    
    WHY each field:
    - title: Quick identification in lists/search
    - entry_type: Domain categorization for filtering
    - source_url: Reference back to original problem/resource
    - difficulty: Self-assessed, helps track progress in difficulty levels
    - time_spent_minutes: Awareness of time investment
    - is_complete: Allows saving drafts, but incomplete entries don't count
    - embedding: Future hook for semantic search (stores vector as JSON)
    """
    __tablename__ = "entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core identification
    title = Column(String(500), nullable=False, index=True)
    entry_type = Column(Enum(EntryType), nullable=False, index=True)
    
    # Context fields
    source_url = Column(String(2000), nullable=True)  # LeetCode link, docs, etc.
    source_name = Column(String(200), nullable=True)  # "LeetCode", "Codeforces", etc.
    
    # Metadata
    difficulty = Column(Integer, nullable=True)  # 1-5 scale, user-defined
    time_spent_minutes = Column(Integer, nullable=True)
    
    # Solution/code (optional - this is NOT the focus)
    code_snippet = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)  # python, cpp, etc.
    
    # Completion tracking
    # WHY: Entry must have reflection to be considered complete
    is_complete = Column(Boolean, default=False, index=True)
    has_reflection = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Future: Embedding for semantic search
    # Stored as JSON string of float array
    embedding = Column(Text, nullable=True)
    
    # Relationships
    reflection = relationship(
        "Reflection", 
        back_populates="entry", 
        uselist=False,  # One-to-one
        cascade="all, delete-orphan"
    )
    
    patterns = relationship(
        "EntryPattern",
        back_populates="entry",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Entry(id={self.id}, title='{self.title[:30]}...', type={self.entry_type.value})>"
