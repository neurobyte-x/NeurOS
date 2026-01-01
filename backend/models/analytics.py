"""
Analytics models - tracking learning patterns over time.

WHY: The intelligence layer needs historical data to:
- Identify repeated blockers (you keep getting stuck on the same thing)
- Track pattern evolution (which patterns are you mastering?)
- Suggest revisions (what needs reinforcement?)

These models support the "you struggled with X last 3 times" signals.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Float, Boolean
)
from sqlalchemy.orm import relationship

from database import Base


class BlockerAnalytics(Base):
    """
    Track repeated blockers across entries.
    
    WHY: If you keep getting stuck on "off-by-one errors in binary search"
    or "async/await confusion", the system should notice and help you
    address the root cause.
    
    DESIGN: Extracted from reflections' initial_blocker field.
    Fuzzy matching or embedding similarity groups similar blockers.
    """
    __tablename__ = "blocker_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    blocker_text = Column(Text, nullable=False)
    
    blocker_category = Column(String(200), nullable=True, index=True)
    
    occurrence_count = Column(Integer, default=1)
    entry_ids = Column(Text, nullable=False)
    
    times_resolved = Column(Integer, default=0)
    avg_resolution_time_minutes = Column(Float, nullable=True)
    
    is_flagged = Column(Boolean, default=False, index=True)
    
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BlockerAnalytics(id={self.id}, count={self.occurrence_count})>"


class RevisionHistory(Base):
    """
    Track when entries/patterns were reviewed.
    
    WHY: Spaced repetition is powerful. This model tracks:
    - When you last reviewed something
    - How your confidence changed over reviews
    - What needs revision based on time decay
    
    FUTURE: Can implement SM-2 or similar algorithm.
    """
    __tablename__ = "revision_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=True)
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)
    
    revision_type = Column(String(50), nullable=False)
    
    recall_quality = Column(Integer, nullable=False)
    confidence_after = Column(Integer, nullable=True)
    
    revision_notes = Column(Text, nullable=True)
    
    time_spent_minutes = Column(Integer, nullable=True)
    
    revised_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    next_review_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self):
        return f"<RevisionHistory(id={self.id}, type='{self.revision_type}')>"


class DailyStats(Base):
    """
    Daily aggregated statistics.
    
    WHY: Quick dashboard view of daily progress without
    expensive queries across all entries.
    """
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    entries_total = Column(Integer, default=0)
    entries_dsa = Column(Integer, default=0)
    entries_backend = Column(Integer, default=0)
    entries_ai_ml = Column(Integer, default=0)
    entries_debug = Column(Integer, default=0)
    entries_interview = Column(Integer, default=0)
    
    patterns_used = Column(Integer, default=0)
    new_patterns = Column(Integer, default=0)
    
    total_time_minutes = Column(Integer, default=0)
    avg_time_to_insight = Column(Float, nullable=True)
    
    blockers_encountered = Column(Integer, default=0)
    repeated_blockers = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<DailyStats(date={self.date}, entries={self.entries_total})>"
