"""
Reflection schemas - the mandatory thinking capture.

WHY: Strict validation ensures no entry can be completed
without proper reflection. This is the core differentiator
of Thinking OS from generic note-taking apps.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ReflectionBase(BaseModel):
    """
    Base reflection fields with strict validation.
    
    WHY: All mandatory fields have validators to ensure
    they're not empty strings or whitespace-only.
    """
    
    context: str = Field(
        ..., 
        min_length=10,
        description="What were you trying to solve/build? (minimum 10 chars)"
    )
    initial_blocker: str = Field(
        ...,
        min_length=10,
        description="Why were you stuck or unsure? (minimum 10 chars)"
    )
    trigger_signal: str = Field(
        ...,
        min_length=5,
        description="What revealed the correct direction? (minimum 5 chars)"
    )
    key_pattern: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Name the pattern in your own words (minimum 3 chars)"
    )
    mistake_or_edge_case: str = Field(
        ...,
        min_length=5,
        description="One mistake or edge case to remember (minimum 5 chars)"
    )
    
    time_to_insight_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="How long until the breakthrough?"
    )
    additional_notes: Optional[str] = Field(
        None,
        description="Any additional thoughts"
    )
    next_time_strategy: Optional[str] = Field(
        None,
        description="What would you do differently next time?"
    )
    confidence_level: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="How confident are you about this pattern? (1-5)"
    )
    
    @field_validator('context', 'initial_blocker', 'trigger_signal', 
                     'key_pattern', 'mistake_or_edge_case', mode='before')
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        """
        Strip whitespace and ensure meaningful content.
        
        WHY: Prevents gaming the system with spaces/newlines.
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("This field cannot be empty or whitespace only")
        return v


class ReflectionCreate(ReflectionBase):
    """
    Schema for creating a reflection.
    
    WHY: Forces all mandatory fields at creation time.
    No reflection → no completed entry.
    """
    entry_id: int = Field(..., description="Entry this reflection belongs to")
    
    @model_validator(mode='after')
    def validate_meaningful_reflection(self):
        """
        Ensure reflection has substantive content.
        
        WHY: Prevent low-effort reflections like 
        "just solved it" or "it worked".
        """
        if self.context.lower() == self.initial_blocker.lower():
            raise ValueError(
                "Context and Initial Blocker should be different. "
                "Context is what you were doing, Blocker is why you were stuck."
            )
        
        return self


class ReflectionUpdate(BaseModel):
    """
    Schema for updating a reflection.
    
    WHY: All fields optional for partial updates,
    but mandatory fields can't be set to empty.
    """
    context: Optional[str] = Field(None, min_length=10)
    initial_blocker: Optional[str] = Field(None, min_length=10)
    trigger_signal: Optional[str] = Field(None, min_length=5)
    key_pattern: Optional[str] = Field(None, min_length=3, max_length=500)
    mistake_or_edge_case: Optional[str] = Field(None, min_length=5)
    time_to_insight_minutes: Optional[int] = Field(None, ge=0)
    additional_notes: Optional[str] = None
    next_time_strategy: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=5)


class ReflectionResponse(ReflectionBase):
    """Schema for reflection in API responses."""
    id: int
    entry_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
