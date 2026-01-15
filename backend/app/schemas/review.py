"""
NeurOS 2.0 Review Schemas

Pydantic schemas for SRS reviews and flash-coding practice.
"""

from datetime import datetime
from typing import Optional, Any, Union

from pydantic import BaseModel, Field, ConfigDict

from app.models.srs_review import ReviewItemType, ReviewStatus


# =============================================================================
# Review Item Schemas
# =============================================================================

class ReviewItemBase(BaseModel):
    """Base schema for review items."""
    item_type: ReviewItemType
    item_id: int


class ReviewItemCreate(ReviewItemBase):
    """Schema for creating a review item."""
    pass


class ReviewItemResponse(ReviewItemBase):
    """Schema for review item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    interval_days: int
    ease_factor: float
    repetition_number: int
    status: ReviewStatus
    next_review_at: datetime
    last_review_at: Optional[datetime]
    review_count: int
    lapse_count: int
    last_quality: Optional[int]
    is_suspended: bool
    is_leech: bool
    created_at: datetime
    
    # Computed
    is_due: bool = False
    is_overdue: bool = False


class ReviewItemWithData(ReviewItemResponse):
    """Review item with the actual item data loaded."""
    item_data: dict[str, Any]  # Entry, Pattern, or custom data


# =============================================================================
# Review Submission Schemas
# =============================================================================

class ReviewSubmit(BaseModel):
    """Schema for submitting a review."""
    quality: int = Field(..., ge=0, le=5, description="Recall quality 0-5")
    time_taken_seconds: Optional[int] = Field(None, ge=0)
    
    # For flash-coding
    user_code: Optional[str] = None
    self_rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewResult(BaseModel):
    """Schema for review result after submission."""
    review_id: int
    new_interval_days: int
    new_ease_factor: float
    next_review_at: datetime
    is_graduated: bool
    repetition_number: int
    
    # Feedback
    message: str
    improvement_tip: Optional[str] = None


# =============================================================================
# Review Queue Schemas
# =============================================================================

class ReviewQueueStats(BaseModel):
    """Schema for review queue statistics."""
    due_now: int
    due_today: int
    learning_count: int
    review_count: int
    overdue_count: int
    estimated_time_minutes: int


class ReviewQueue(BaseModel):
    """Schema for the review queue."""
    stats: ReviewQueueStats
    items: list[ReviewItemWithData]
    next_item: Optional[ReviewItemWithData] = None


# =============================================================================
# Flash Coding Schemas
# =============================================================================

class FlashCodingProblem(BaseModel):
    """Schema for a flash-coding practice problem."""
    review_item_id: int
    pattern_name: str
    pattern_description: Optional[str]
    when_to_use: str
    example_problem: Optional[str]
    language: str
    time_limit_seconds: int = 600  # 10 minutes default
    
    # Hidden until revealed
    template_code: Optional[str] = None
    key_insight: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None


class FlashCodingSubmission(BaseModel):
    """Schema for flash-coding submission."""
    review_item_id: int
    user_code: str
    time_taken_seconds: int
    self_rating: int = Field(..., ge=1, le=5, description="Self-assessment 1-5")
    reveal_requested: bool = False


class FlashCodingResult(BaseModel):
    """Schema for flash-coding result."""
    review_result: ReviewResult
    original_code: str
    similarity_score: Optional[float] = None  # If we implement code comparison
    feedback: str


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkReviewCreate(BaseModel):
    """Schema for creating multiple review items."""
    items: list[ReviewItemCreate]


class BulkReviewResult(BaseModel):
    """Schema for bulk review creation result."""
    created: int
    skipped: int
    errors: list[str]
