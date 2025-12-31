"""
Entry schemas for request/response validation.

WHY: Pydantic schemas provide:
- Input validation with clear error messages
- Response serialization
- API documentation (OpenAPI)
- Type safety across the application
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from models.entry import EntryType


class EntryBase(BaseModel):
    """Base entry fields shared across schemas."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Entry title")
    entry_type: EntryType = Field(..., description="Domain category")
    source_url: Optional[str] = Field(None, max_length=2000, description="Source link")
    source_name: Optional[str] = Field(None, max_length=200, description="Source name")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty 1-5")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent")
    code_snippet: Optional[str] = Field(None, description="Code solution (optional)")
    language: Optional[str] = Field(None, max_length=50, description="Programming language")


class EntryCreate(EntryBase):
    """
    Schema for creating a new entry.
    
    WHY: Separate from EntryBase to potentially add
    creation-specific fields or validation later.
    """
    pass


class EntryUpdate(BaseModel):
    """
    Schema for updating an entry.
    
    WHY: All fields optional to support partial updates.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    entry_type: Optional[EntryType] = None
    source_url: Optional[str] = Field(None, max_length=2000)
    source_name: Optional[str] = Field(None, max_length=200)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    time_spent_minutes: Optional[int] = Field(None, ge=0)
    code_snippet: Optional[str] = None
    language: Optional[str] = Field(None, max_length=50)


class EntryResponse(EntryBase):
    """
    Schema for entry in API responses.
    
    WHY: Includes computed fields and relationships
    not present in create/update schemas.
    """
    id: int
    is_complete: bool
    has_reflection: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReflectionInEntry(BaseModel):
    """Nested reflection data in entry response."""
    id: int
    context: str
    initial_blocker: str
    trigger_signal: str
    key_pattern: str
    mistake_or_edge_case: str
    confidence_level: Optional[int]
    next_time_strategy: Optional[str]
    
    class Config:
        from_attributes = True


class PatternInEntry(BaseModel):
    """Nested pattern data in entry response."""
    id: int
    name: str
    description: Optional[str]
    relevance_score: float
    
    class Config:
        from_attributes = True


class EntryWithReflection(EntryResponse):
    """
    Full entry response including reflection and patterns.
    
    WHY: Used when fetching a single entry for detailed view.
    Includes all nested data to avoid N+1 queries.
    """
    reflection: Optional[ReflectionInEntry] = None
    patterns: List[PatternInEntry] = []
    
    class Config:
        from_attributes = True


class EntryListResponse(BaseModel):
    """
    Paginated list of entries.
    
    WHY: Pagination support for large datasets.
    """
    entries: List[EntryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
