"""
NeurOS 2.0 Standup Schemas

Pydantic schemas for daily standup / morning plan.
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.review import ReviewItemWithData
from app.schemas.entry import EntryResponse
from app.schemas.decay import DecayCriticalAlert


# =============================================================================
# Daily Plan Schemas
# =============================================================================

class DailyPlanStats(BaseModel):
    """Quick stats for the daily plan."""
    current_streak: int
    total_reviews_pending: int
    estimated_time_minutes: int
    reviews_completed_today: int
    daily_goal: int
    goal_progress_percent: float


class SuggestedChallenge(BaseModel):
    """A suggested new learning challenge."""
    entry_type: str
    title: str
    description: str
    estimated_time_minutes: int
    reason: str  # Why this is suggested
    tags: list[str]
    
    # Optional: Link to external resource
    resource_url: Optional[str] = None


class WeakAreaAlert(BaseModel):
    """Alert for a weak area needing attention."""
    domain: str
    pattern_or_concept: str
    decay_score: int
    times_struggled: int
    last_seen: Optional[datetime]
    suggestion: str


class DailyPlan(BaseModel):
    """Complete daily plan for the morning standup."""
    date: date
    greeting: str  # Personalized greeting
    stats: DailyPlanStats
    
    # Priority sections
    high_priority_reviews: list[ReviewItemWithData]  # Decay < 40
    scheduled_reviews: list[ReviewItemWithData]       # Due today
    
    # Learning
    suggested_challenge: Optional[SuggestedChallenge] = None
    
    # Alerts
    weak_areas: list[WeakAreaAlert]
    critical_decay_items: list[DecayCriticalAlert]
    
    # Motivation
    motivation_message: Optional[str] = None
    achievement_unlocked: Optional[str] = None


# =============================================================================
# Session Planning Schemas
# =============================================================================

class StudySessionPlan(BaseModel):
    """Detailed plan for a study session."""
    duration_minutes: int
    
    # Ordered activities
    activities: list[dict]  # [{type, item_id, estimated_minutes}]
    
    # Breaks
    include_breaks: bool = True
    break_interval_minutes: int = 25  # Pomodoro style
    
    # Goals
    review_goal: int
    new_learning_goal: int


class SessionStart(BaseModel):
    """Response when starting a study session."""
    session_id: str
    plan: StudySessionPlan
    first_item: Optional[ReviewItemWithData]
    started_at: datetime


class SessionEnd(BaseModel):
    """Response when ending a study session."""
    session_id: str
    duration_minutes: int
    reviews_completed: int
    new_items_learned: int
    average_quality: float
    streak_maintained: bool
    xp_earned: int  # Gamification


# =============================================================================
# Standup History
# =============================================================================

class StandupHistory(BaseModel):
    """Historical standup data for trends."""
    date: date
    reviews_planned: int
    reviews_completed: int
    completion_rate: float
    average_quality: float
    time_spent_minutes: int


class WeeklyReport(BaseModel):
    """Weekly progress report."""
    week_start: date
    week_end: date
    
    # Summary
    total_reviews: int
    total_time_minutes: int
    average_daily_reviews: float
    
    # By day
    daily_history: list[StandupHistory]
    
    # Achievements
    patterns_mastered: list[str]
    entries_completed: int
    streak_days: int
    
    # Areas for improvement
    struggling_areas: list[WeakAreaAlert]
    
    # Next week focus
    recommended_focus: list[str]
