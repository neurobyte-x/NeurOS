"""
Learning Plan schemas for request/response validation.

WHY: Clear API contracts for the learning plan system.
Users can create plans, track progress, and adapt their roadmap.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from models.learning_plan import PlanType, PlanStatus, MilestoneStatus


class CreatePlanRequest(BaseModel):
    """
    Request to generate a new learning plan.
    
    WHY: We need context about the user's goals, current level,
    and available time to create a personalized plan.
    """
    plan_type: PlanType = Field(..., description="Type of plan to create")
    
    primary_goal: str = Field(
        ..., 
        min_length=10,
        max_length=500,
        description="Main objective (e.g., 'Crack FAANG interviews in 3 months')"
    )
    secondary_goals: Optional[List[str]] = Field(
        None,
        description="Additional goals"
    )
    
    start_date: Optional[date] = Field(
        None, 
        description="When to start (default: today)"
    )
    target_weeks: int = Field(
        default=12,
        ge=1,
        le=52,
        description="Target duration in weeks"
    )
    daily_time_minutes: int = Field(
        default=60,
        ge=15,
        le=480,
        description="Time available per day (minutes)"
    )
    weekly_days: int = Field(
        default=5,
        ge=1,
        le=7,
        description="Days per week available"
    )
    
    current_dsa_level: Optional[int] = Field(None, ge=1, le=10)
    current_cp_level: Optional[int] = Field(None, ge=1, le=10)
    current_backend_level: Optional[int] = Field(None, ge=1, le=10)
    current_ai_ml_level: Optional[int] = Field(None, ge=1, le=10)
    
    target_dsa_level: Optional[int] = Field(None, ge=1, le=10)
    target_cp_level: Optional[int] = Field(None, ge=1, le=10)
    target_backend_level: Optional[int] = Field(None, ge=1, le=10)
    target_ai_ml_level: Optional[int] = Field(None, ge=1, le=10)
    
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific topics to focus on"
    )
    avoid_areas: Optional[List[str]] = Field(
        None,
        description="Topics to skip or de-prioritize"
    )
    preferred_resources: Optional[List[str]] = Field(
        None,
        description="Preferred learning resources (NeetCode, LeetCode, etc.)"
    )


class UpdatePlanRequest(BaseModel):
    """Update plan settings."""
    title: Optional[str] = None
    status: Optional[PlanStatus] = None
    daily_time_minutes: Optional[int] = Field(None, ge=15, le=480)
    weekly_days: Optional[int] = Field(None, ge=1, le=7)
    target_end_date: Optional[date] = None


class MilestoneUpdateRequest(BaseModel):
    """Update milestone status."""
    status: Optional[MilestoneStatus] = None
    reflection_notes: Optional[str] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)


class CompleteTaskRequest(BaseModel):
    """Mark a daily task as complete."""
    actual_minutes: Optional[int] = None
    notes: Optional[str] = None


class AdaptPlanRequest(BaseModel):
    """
    Request to adapt/modify the plan based on progress.
    
    WHY: Plans should evolve based on actual performance.
    """
    reason: str = Field(
        ...,
        description="Why adapting (e.g., 'Too difficult', 'Ahead of schedule')"
    )
    new_daily_time: Optional[int] = Field(None, ge=15, le=480)
    extend_weeks: Optional[int] = Field(None, ge=0, le=12)
    shift_focus: Optional[List[str]] = None


class DailyTaskResponse(BaseModel):
    """Individual task in a schedule."""
    id: int
    title: str
    description: Optional[str] = None
    task_type: str
    day_of_week: int
    scheduled_date: Optional[date] = None
    resource_url: Optional[str] = None
    resource_name: Optional[str] = None
    estimated_minutes: int
    actual_minutes: Optional[int] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class WeeklyScheduleResponse(BaseModel):
    """Weekly breakdown of tasks."""
    id: int
    week_number: int
    week_start_date: Optional[date] = None
    week_end_date: Optional[date] = None
    theme: Optional[str] = None
    focus_areas: List[str] = []
    daily_tasks: Dict[str, Any] = {}
    weekly_goals: List[str] = []
    problems_to_solve: int
    concepts_to_learn: int
    is_completed: bool
    completion_notes: Optional[str] = None
    actual_time_spent: Optional[int] = None
    
    class Config:
        from_attributes = True


class MilestoneResponse(BaseModel):
    """Milestone in a learning plan."""
    id: int
    title: str
    description: str
    order_index: int
    topics: List[str] = []
    skills_to_gain: List[str] = []
    success_criteria: Optional[str] = None
    estimated_days: Optional[int] = None
    target_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: MilestoneStatus
    recommended_resources: List[dict] = []
    recommended_problems: List[dict] = []
    tasks_total: int
    tasks_completed: int
    reflection_notes: Optional[str] = None
    difficulty_rating: Optional[int] = None
    
    class Config:
        from_attributes = True


class LearningPlanResponse(BaseModel):
    """Full learning plan response."""
    id: int
    title: str
    description: str
    plan_type: PlanType
    status: PlanStatus
    primary_goal: str
    secondary_goals: List[str] = []
    target_outcome: Optional[str] = None
    
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    daily_time_minutes: int
    weekly_days: int
    
    initial_dsa_level: Optional[int] = None
    initial_cp_level: Optional[int] = None
    initial_backend_level: Optional[int] = None
    initial_ai_ml_level: Optional[int] = None
    target_dsa_level: Optional[int] = None
    target_cp_level: Optional[int] = None
    target_backend_level: Optional[int] = None
    target_ai_ml_level: Optional[int] = None
    
    total_milestones: int
    completed_milestones: int
    progress_percentage: float
    current_week: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LearningPlanSummary(BaseModel):
    """Brief plan summary for lists."""
    id: int
    title: str
    plan_type: PlanType
    status: PlanStatus
    progress_percentage: float
    current_week: int
    target_end_date: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LearningPlanWithDetails(LearningPlanResponse):
    """Plan with milestones and schedules."""
    milestones: List[MilestoneResponse] = []
    weekly_schedules: List[WeeklyScheduleResponse] = []


class TodaysTasks(BaseModel):
    """Tasks for today across all active plans."""
    date: date
    total_tasks: int
    completed_tasks: int
    pending_tasks: List[DailyTaskResponse]
    estimated_total_minutes: int
    plans_involved: List[LearningPlanSummary]


class WeeklyProgress(BaseModel):
    """Weekly progress summary."""
    week_number: int
    plan_id: int
    plan_title: str
    theme: Optional[str]
    tasks_total: int
    tasks_completed: int
    time_spent_minutes: int
    goals_achieved: List[str]
    goals_pending: List[str]


class PlanDashboard(BaseModel):
    """Dashboard data for learning plans."""
    active_plans: List[LearningPlanSummary]
    todays_tasks: TodaysTasks
    current_week_progress: List[WeeklyProgress]
    upcoming_milestones: List[MilestoneResponse]
    overall_stats: dict
