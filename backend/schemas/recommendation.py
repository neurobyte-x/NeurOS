"""
Recommendation schemas for request/response validation.

WHY: Clear API contracts for the recommendation system.
Users can request recommendations, view them, and provide feedback.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from models.recommendation import (
    RecommendationType, 
    RecommendationPriority,
    RecommendationDomain
)


# === Request Schemas ===

class GenerateRecommendationsRequest(BaseModel):
    """
    Request to generate personalized recommendations.
    
    WHY: Context helps AI generate better recommendations.
    """
    domains: Optional[List[RecommendationDomain]] = Field(
        None, 
        description="Focus areas (dsa, cp, backend, ai_ml). None = all"
    )
    count: int = Field(
        default=5, 
        ge=1, 
        le=20, 
        description="Number of recommendations to generate"
    )
    include_revisions: bool = Field(
        default=True,
        description="Include revision recommendations for past struggles"
    )
    difficulty_preference: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Preferred difficulty level"
    )
    available_time_minutes: Optional[int] = Field(
        None, 
        ge=15, 
        description="Time available for recommended tasks"
    )
    current_focus: Optional[str] = Field(
        None, 
        max_length=500,
        description="What you're currently working on/preparing for"
    )


class RecommendationFeedback(BaseModel):
    """User feedback on a recommendation."""
    user_rating: int = Field(..., ge=1, le=5, description="How helpful (1-5)")
    user_feedback: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")


class RecommendationUpdate(BaseModel):
    """Update a recommendation's status."""
    is_completed: Optional[bool] = None
    is_dismissed: Optional[bool] = None


# === Response Schemas ===

class RecommendationBase(BaseModel):
    """Base recommendation fields."""
    title: str
    description: str
    rec_type: RecommendationType
    domain: RecommendationDomain
    priority: RecommendationPriority
    reasoning: str


class RecommendationResponse(RecommendationBase):
    """Full recommendation response."""
    id: int
    resource_url: Optional[str] = None
    resource_name: Optional[str] = None
    difficulty_level: Optional[int] = None
    estimated_minutes: Optional[int] = None
    related_patterns: List[str] = []
    prerequisites: List[str] = []
    is_completed: bool = False
    is_dismissed: bool = False
    completed_at: Optional[datetime] = None
    user_rating: Optional[int] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RecommendationSummary(BaseModel):
    """Brief recommendation for lists."""
    id: int
    title: str
    rec_type: RecommendationType
    domain: RecommendationDomain
    priority: RecommendationPriority
    estimated_minutes: Optional[int] = None
    is_completed: bool
    is_dismissed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationsListResponse(BaseModel):
    """Paginated list of recommendations."""
    recommendations: List[RecommendationResponse]
    total: int
    pending_count: int
    completed_count: int
    dismissed_count: int


class QuickRecommendation(BaseModel):
    """
    Quick recommendation without persistence.
    Used for instant suggestions based on current context.
    """
    title: str
    description: str
    rec_type: str
    domain: str
    reasoning: str
    resource_url: Optional[str] = None
    estimated_minutes: Optional[int] = None
    difficulty_level: Optional[int] = None


class SkillGapAnalysis(BaseModel):
    """
    Analysis of user's skill gaps.
    Used to explain WHY certain recommendations are made.
    """
    domain: str
    current_level: int  # 1-10
    identified_gaps: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    suggested_focus: str


class RecommendationDashboard(BaseModel):
    """
    Dashboard data for recommendations section.
    """
    active_recommendations: List[RecommendationSummary]
    skill_gaps: List[SkillGapAnalysis]
    daily_suggestion: Optional[QuickRecommendation] = None
    weekly_focus: Optional[str] = None
    stats: dict  # Completion rates, etc.
