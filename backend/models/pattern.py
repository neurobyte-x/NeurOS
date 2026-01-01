"""
Pattern model - reusable thinking patterns across domains.

WHY: Patterns are the transferable units of knowledge.
A pattern like "state compression" applies to:
- DSA: Bitmask DP
- Backend: Caching strategies  
- AI/ML: Feature encoding

By naming patterns in YOUR words, you build a personal
vocabulary that accelerates recognition in new contexts.

DESIGN: Many-to-many relationship with entries allows:
- One entry to demonstrate multiple patterns
- One pattern to appear across many entries
- Pattern strength to grow with usage
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Float
)
from sqlalchemy.orm import relationship

from database import Base


class Pattern(Base):
    """
    User-defined thinking pattern.
    
    WHY each field:
    - name: User's own terminology (not textbook)
    - description: What this pattern means to YOU
    - domain_tags: Which domains this applies to
    - usage_count: How often you've seen this (auto-tracked)
    - success_rate: How often recognizing this led to success
    """
    __tablename__ = "patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(200), nullable=False, unique=True, index=True)
    
    description = Column(Text, nullable=True)
    
    domain_tags = Column(String(500), nullable=True)
    
    common_triggers = Column(Text, nullable=True)
    
    common_mistakes = Column(Text, nullable=True)
    
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    entries = relationship("EntryPattern", back_populates="pattern")
    
    def __repr__(self):
        return f"<Pattern(id={self.id}, name='{self.name}')>"


class EntryPattern(Base):
    """
    Many-to-many relationship between entries and patterns.
    
    WHY separate table:
    - Store relationship-specific data (confidence, notes)
    - Track when a pattern was associated
    - Allow pattern strength per entry
    """
    __tablename__ = "entry_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=False)
    
    relevance_score = Column(Float, default=1.0)
    
    application_notes = Column(Text, nullable=True)
    
    was_successful = Column(Integer, default=1)  # 1=yes, 0=no, -1=partial
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    entry = relationship("Entry", back_populates="patterns")
    pattern = relationship("Pattern", back_populates="entries")
    
    def __repr__(self):
        return f"<EntryPattern(entry_id={self.entry_id}, pattern_id={self.pattern_id})>"
