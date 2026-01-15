"""
NeurOS 2.0 Pattern Schemas

Pydantic schemas for thinking patterns.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.pattern_template import ProgrammingLanguage


# =============================================================================
# Template Schemas (nested)
# =============================================================================

class PatternTemplateCreate(BaseModel):
    """Schema for creating a pattern template."""
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    template_code: str = Field(..., min_length=1)
    when_to_use: Optional[str] = None
    example_problem: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    key_insight: Optional[str] = None
    common_mistakes: Optional[str] = None
    difficulty_rating: int = Field(50, ge=1, le=100)


class PatternTemplateResponse(BaseModel):
    """Schema for pattern template response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    pattern_id: int
    language: ProgrammingLanguage
    template_code: str
    when_to_use: Optional[str]
    example_problem: Optional[str]
    time_complexity: Optional[str]
    space_complexity: Optional[str]
    key_insight: Optional[str]
    common_mistakes: Optional[str]
    difficulty_rating: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Pattern Schemas
# =============================================================================

class PatternBase(BaseModel):
    """Base pattern schema."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=50)
    when_to_use: Optional[str] = None
    common_triggers: Optional[str] = None
    common_mistakes: Optional[str] = None


class PatternCreate(PatternBase):
    """Schema for creating a pattern."""
    pass


class PatternUpdate(BaseModel):
    """Schema for updating a pattern."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=50)
    when_to_use: Optional[str] = None
    common_triggers: Optional[str] = None
    common_mistakes: Optional[str] = None


class PatternResponse(PatternBase):
    """Schema for pattern response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    usage_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    success_rate: Optional[float] = None
    is_cross_domain: bool = False


class PatternWithTemplates(PatternResponse):
    """Pattern response with templates."""
    templates: list[PatternTemplateResponse] = []


class PatternWithEntries(PatternResponse):
    """Pattern response with linked entries."""
    # Use forward reference to avoid circular import
    linked_entries: list["EntryResponse"] = []


# Import EntryResponse for forward reference resolution
from app.schemas.entry import EntryResponse

PatternWithEntries.model_rebuild()


class PatternListResponse(BaseModel):
    """Schema for paginated pattern list."""
    items: list[PatternResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Pattern Usage Schemas
# =============================================================================

class PatternUsageRecord(BaseModel):
    """Schema for recording pattern usage."""
    pattern_id: int
    entry_id: int
    was_successful: bool = True


class PatternStats(BaseModel):
    """Schema for pattern statistics."""
    pattern_id: int
    pattern_name: str
    usage_count: int
    success_rate: Optional[float]
    domains_used: list[str]
    recent_entries_count: int
    decay_score: Optional[int]
