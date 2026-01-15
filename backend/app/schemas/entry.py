"""
NeurOS 2.0 Entry Schemas

Pydantic schemas for learning entries.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from app.models.entry import EntryType, DifficultyLevel


# =============================================================================
# Base Schemas
# =============================================================================

class EntryBase(BaseModel):
    """Base entry schema."""
    title: str = Field(..., min_length=1, max_length=500)
    entry_type: EntryType = EntryType.CONCEPT
    problem_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    difficulty: Optional[DifficultyLevel] = None
    time_spent_minutes: Optional[int] = Field(None, ge=0)


# =============================================================================
# Request Schemas
# =============================================================================

class EntryCreate(EntryBase):
    """Schema for creating a new entry."""
    pass


class EntryUpdate(BaseModel):
    """Schema for updating an entry."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    entry_type: Optional[EntryType] = None
    problem_url: Optional[str] = None
    tags: Optional[list[str]] = None
    difficulty: Optional[DifficultyLevel] = None
    time_spent_minutes: Optional[int] = Field(None, ge=0)


# =============================================================================
# Reflection Schemas (nested)
# =============================================================================

class ReflectionCreate(BaseModel):
    """Schema for creating a reflection (completes the entry)."""
    problem_context: str = Field(..., min_length=10, description="What problem were you solving?")
    initial_blocker: str = Field(..., min_length=10, description="What blocked your progress?")
    trigger_signal: str = Field(..., min_length=10, description="What insight led to understanding?")
    key_pattern: str = Field(..., min_length=5, description="Name the pattern in your words")
    mistakes_edge_cases: str = Field(..., min_length=5, description="What to remember?")
    
    # Optional extended reflection
    what_i_would_do_differently: Optional[str] = None
    related_concepts: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=5)


class ReflectionResponse(BaseModel):
    """Schema for reflection response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    entry_id: int
    problem_context: str
    initial_blocker: str
    trigger_signal: str
    key_pattern: str
    mistakes_edge_cases: str
    what_i_would_do_differently: Optional[str]
    related_concepts: Optional[str]
    confidence_level: Optional[int]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Response Schemas
# =============================================================================

class EntryResponse(EntryBase):
    """Schema for entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_completed: bool
    completed_at: Optional[datetime]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested reflection (if completed)
    reflection: Optional[ReflectionResponse] = None


class EntryWithDecay(EntryResponse):
    """Entry response with decay information."""
    decay_score: Optional[int] = None
    decay_status: Optional[str] = None
    next_review_date: Optional[datetime] = None


class EntryListResponse(BaseModel):
    """Schema for paginated entry list."""
    items: list[EntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Filter/Query Schemas
# =============================================================================

class EntryFilter(BaseModel):
    """Schema for filtering entries."""
    entry_type: Optional[EntryType] = None
    is_completed: Optional[bool] = None
    difficulty: Optional[DifficultyLevel] = None
    tags: Optional[list[str]] = None
    search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
