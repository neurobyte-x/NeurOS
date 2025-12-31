"""
Pattern schemas - user-defined thinking patterns.

WHY: Patterns are how knowledge becomes transferable.
These schemas support creating, searching, and analyzing
patterns across domains.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class PatternBase(BaseModel):
    """Base pattern fields."""
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Pattern name in your own words"
    )
    description: Optional[str] = Field(
        None,
        description="What this pattern means to you"
    )
    domain_tags: Optional[str] = Field(
        None,
        max_length=500,
        description="Comma-separated domain tags (e.g., 'dsa,backend')"
    )
    common_triggers: Optional[str] = Field(
        None,
        description="What clues suggest this pattern applies?"
    )
    common_mistakes: Optional[str] = Field(
        None,
        description="Common mistakes when applying this pattern"
    )
    
    @field_validator('name', mode='before')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """
        Normalize pattern name for consistency.
        
        WHY: Prevents duplicate patterns with different casing/spacing.
        """
        if isinstance(v, str):
            # Strip, lowercase for comparison, but keep original case
            v = v.strip()
        return v


class PatternCreate(PatternBase):
    """Schema for creating a new pattern."""
    pass


class PatternUpdate(BaseModel):
    """Schema for updating a pattern."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    domain_tags: Optional[str] = Field(None, max_length=500)
    common_triggers: Optional[str] = None
    common_mistakes: Optional[str] = None


class PatternResponse(PatternBase):
    """Schema for pattern in API responses."""
    id: int
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EntryInPattern(BaseModel):
    """Nested entry data in pattern response."""
    id: int
    title: str
    entry_type: str
    created_at: datetime
    relevance_score: float
    
    class Config:
        from_attributes = True


class PatternWithEntries(PatternResponse):
    """
    Full pattern response with related entries.
    
    WHY: Shows all entries demonstrating this pattern,
    useful for revision and pattern analysis.
    """
    entries: List[EntryInPattern] = []
    
    class Config:
        from_attributes = True


class EntryPatternCreate(BaseModel):
    """
    Schema for associating a pattern with an entry.
    
    WHY: Separate schema for the many-to-many relationship
    with relationship-specific metadata.
    """
    entry_id: int
    pattern_id: Optional[int] = None  # If linking to existing pattern
    pattern_name: Optional[str] = None  # If creating new pattern inline
    relevance_score: float = Field(1.0, ge=0.0, le=1.0)
    application_notes: Optional[str] = None
    was_successful: int = Field(1, ge=-1, le=1)  # -1=partial, 0=no, 1=yes
    
    @field_validator('pattern_id', 'pattern_name', mode='before')
    @classmethod
    def validate_pattern_reference(cls, v, info):
        """Ensure at least one pattern reference is provided."""
        return v


class PatternSearchResult(BaseModel):
    """
    Pattern search result with relevance scoring.
    
    WHY: Used by recall system to surface related patterns.
    """
    pattern: PatternResponse
    relevance: float = Field(..., ge=0.0, le=1.0)
    match_reason: str  # Why this pattern was suggested
    
    class Config:
        from_attributes = True
