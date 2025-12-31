"""
Analytics schemas - recall and intelligence layer.

WHY: These schemas power the "smart" features:
- Similar entry suggestions
- Repeated blocker detection
- Revision recommendations
- Progress insights
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BlockerAnalyticsResponse(BaseModel):
    """
    Blocker analysis response.
    
    WHY: Shows repeated blockers to help user
    identify systematic weaknesses.
    """
    id: int
    blocker_text: str
    blocker_category: Optional[str]
    occurrence_count: int
    times_resolved: int
    avg_resolution_time_minutes: Optional[float]
    is_flagged: bool
    first_seen_at: datetime
    last_seen_at: datetime
    related_entry_ids: List[int]
    
    class Config:
        from_attributes = True


class RevisionCreate(BaseModel):
    """Schema for recording a revision session."""
    entry_id: Optional[int] = None
    pattern_id: Optional[int] = None
    revision_type: str = Field(..., description="'entry', 'pattern', or 'blocker'")
    recall_quality: int = Field(..., ge=1, le=5, description="How well did you remember?")
    confidence_after: Optional[int] = Field(None, ge=1, le=5)
    revision_notes: Optional[str] = None
    time_spent_minutes: Optional[int] = Field(None, ge=0)


class RevisionResponse(BaseModel):
    """Schema for revision history in API responses."""
    id: int
    entry_id: Optional[int]
    pattern_id: Optional[int]
    revision_type: str
    recall_quality: int
    confidence_after: Optional[int]
    revision_notes: Optional[str]
    time_spent_minutes: Optional[int]
    revised_at: datetime
    next_review_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DailyStatsResponse(BaseModel):
    """Schema for daily statistics."""
    date: datetime
    entries_total: int
    entries_by_type: dict  # {"dsa": 2, "backend": 1, ...}
    patterns_used: int
    new_patterns: int
    total_time_minutes: int
    avg_time_to_insight: Optional[float]
    blockers_encountered: int
    repeated_blockers: int
    
    class Config:
        from_attributes = True


class RecallSuggestion(BaseModel):
    """
    A suggestion from the recall system.
    
    WHY: Structured suggestions help user decide
    what to review or be aware of before starting work.
    """
    suggestion_type: str = Field(
        ...,
        description="'similar_entry', 'repeated_blocker', 'revision_due', 'pattern_weakness'"
    )
    title: str = Field(..., description="Short description")
    description: str = Field(..., description="Why this is being suggested")
    priority: int = Field(..., ge=1, le=5, description="1=highest priority")
    related_entry_id: Optional[int] = None
    related_pattern_id: Optional[int] = None
    action_text: str = Field(..., description="Suggested action")


class InsightResponse(BaseModel):
    """
    Insights about learning patterns and progress.
    
    WHY: Higher-level analysis to help user understand
    their learning trajectory.
    """
    insight_type: str  # "strength", "weakness", "progress", "suggestion"
    title: str
    description: str
    data: Optional[dict] = None  # Supporting data/stats
    generated_at: datetime


class SimilarEntryResponse(BaseModel):
    """
    Similar entry found by recall system.
    
    WHY: Shows past entries that might be relevant
    to current work, with explanation of similarity.
    """
    entry_id: int
    entry_title: str
    entry_type: str
    similarity_score: float
    similarity_reason: str  # Why this is considered similar
    key_pattern: Optional[str]  # The pattern from this entry
    days_ago: int
    
    class Config:
        from_attributes = True


class RecallContext(BaseModel):
    """
    Context provided to recall system for suggestions.
    
    WHY: User provides context about what they're about
    to work on, system surfaces relevant history.
    """
    title: Optional[str] = None
    entry_type: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class RecallResponse(BaseModel):
    """
    Full recall response with all suggestions.
    
    WHY: Comprehensive response before starting new work
    with similar entries, blockers to watch, patterns to apply.
    """
    similar_entries: List[SimilarEntryResponse] = []
    relevant_patterns: List[dict] = []  # Pattern suggestions
    blocker_warnings: List[str] = []  # "You've struggled with X 3 times"
    revision_suggestions: List[RecallSuggestion] = []
    general_insights: List[InsightResponse] = []
