"""
NeurOS 2.0 Decay Schemas

Pydantic schemas for decay tracking and alerts.
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.decay_tracking import TrackableType
from app.core.decay import DecayStatus


# =============================================================================
# Decay Status Schemas
# =============================================================================

class DecayStatusResponse(BaseModel):
    """Schema for decay status of a single item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trackable_type: TrackableType
    trackable_id: int
    decay_score: int
    status: str
    stability_factor: float
    last_practiced_at: Optional[datetime]
    times_reviewed: int
    next_review_date: Optional[date]
    days_until_critical: Optional[int]
    created_at: datetime
    updated_at: datetime


class DecayStatusWithItem(DecayStatusResponse):
    """Decay status with the actual item data."""
    item_name: str
    item_type: str
    item_domain: Optional[str] = None


# =============================================================================
# Decay Dashboard Schemas
# =============================================================================

class DecayOverview(BaseModel):
    """Overview of decay status across all items."""
    total_tracked: int
    fresh_count: int        # 80-100
    stable_count: int       # 60-79
    decaying_count: int     # 40-59
    critical_count: int     # 20-39
    forgotten_count: int    # 0-19
    
    average_decay_score: float
    items_due_today: int


class DecayCriticalAlert(BaseModel):
    """Alert for critically decaying items."""
    item_id: int
    item_type: TrackableType
    item_name: str
    decay_score: int
    last_practiced_at: Optional[datetime]
    days_since_practice: int
    urgency: str  # "critical", "urgent", "warning"


class DecayDashboard(BaseModel):
    """Full decay dashboard data."""
    overview: DecayOverview
    critical_items: list[DecayCriticalAlert]
    decaying_items: list[DecayStatusWithItem]
    recently_practiced: list[DecayStatusWithItem]
    
    # Trends
    weekly_review_counts: list[int]  # Last 7 days
    average_decay_trend: list[float]  # Last 7 days


# =============================================================================
# Decay Heatmap Schemas
# =============================================================================

class HeatmapDay(BaseModel):
    """Single day in the practice heatmap."""
    date: date
    count: int
    intensity: int  # 0-4 for coloring (like GitHub)


class PracticeHeatmap(BaseModel):
    """Practice consistency heatmap data."""
    days: list[HeatmapDay]
    total_days_practiced: int
    current_streak: int
    longest_streak: int
    start_date: date
    end_date: date


# =============================================================================
# Decay Calculation Schemas
# =============================================================================

class DecayCalculationRequest(BaseModel):
    """Request schema for calculating decay."""
    last_practiced_at: datetime
    times_reviewed: int = 0
    initial_difficulty: int = Field(50, ge=1, le=100)
    last_quality: int = Field(4, ge=0, le=5)


class DecayCalculationResult(BaseModel):
    """Result of decay calculation."""
    decay_score: int
    status: str
    days_until_critical: Optional[int]
    recommended_review_date: datetime
    stability_factor: float


# =============================================================================
# Batch Operations
# =============================================================================

class BatchDecayUpdate(BaseModel):
    """Request to update decay for multiple items after practice."""
    items: list[dict]  # List of {trackable_type, trackable_id, quality}


class BatchDecayResult(BaseModel):
    """Result of batch decay update."""
    updated_count: int
    new_averages: dict[str, float]  # By domain
