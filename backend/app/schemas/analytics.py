"""
NeurOS 2.0 Analytics Schemas

Pydantic schemas for analytics and insights.
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class DailyActivity(BaseModel):
    """Activity for a single day."""
    date: date
    entries_created: int
    entries_completed: int
    reviews_done: int
    patterns_used: int
    time_spent_minutes: int


class WeeklyTrend(BaseModel):
    """Weekly trend data."""
    week_start: date
    entries_count: int
    completion_rate: float
    average_quality: float
    top_domains: list[str]


class MonthlyOverview(BaseModel):
    """Monthly overview."""
    month: str
    total_entries: int
    total_reviews: int
    average_decay_score: float
    patterns_created: int
    patterns_used: int
    most_active_domain: str
    total_time_hours: float


class DomainStats(BaseModel):
    """Statistics for a single domain."""
    domain: str
    entry_count: int
    completed_count: int
    average_difficulty: float
    average_decay_score: float
    top_patterns: list[str]
    common_blockers: list[str]
    time_spent_hours: float


class DomainComparison(BaseModel):
    """Comparison across domains."""
    domains: list[DomainStats]
    strongest_domain: str
    weakest_domain: str
    recommended_focus: str


class PatternAnalytics(BaseModel):
    """Analytics for patterns."""
    total_patterns: int
    cross_domain_patterns: int
    most_used_patterns: list[dict]
    least_used_patterns: list[dict]
    patterns_needing_review: list[dict]
    highest_success_rate: Optional[dict]
    most_versatile: Optional[dict]


class BlockerAnalysis(BaseModel):
    """Analysis of common blockers."""
    total_blockers_logged: int
    most_common_blockers: list[dict]
    blockers_by_domain: dict[str, list[str]]
    improvement_suggestions: list[str]


class TriggerAnalysis(BaseModel):
    """Analysis of trigger signals."""
    total_triggers_logged: int
    most_effective_triggers: list[dict]
    triggers_by_domain: dict[str, list[str]]


class LearningInsights(BaseModel):
    """Overall learning insights."""
    blocker_analysis: BlockerAnalysis
    trigger_analysis: TriggerAnalysis
    areas_for_improvement: list[str]
    strengths: list[str]
    suggested_next_topics: list[str]


class ProgressMetrics(BaseModel):
    """Progress tracking metrics."""
    total_entries: int
    entries_this_week: int
    entries_this_month: int
    total_reviews: int
    reviews_this_week: int
    average_decay_score: float
    decay_trend: str
    streak_current: int
    streak_longest: int
    mastery_level_distribution: dict[int, int]


class ProgressMilestone(BaseModel):
    """Achievement milestone."""
    name: str
    description: str
    achieved_at: Optional[datetime]
    progress_percent: float


class ProgressReport(BaseModel):
    """Complete progress report."""
    metrics: ProgressMetrics
    milestones: list[ProgressMilestone]
    vs_last_week: dict[str, float]
    vs_last_month: dict[str, float]
    insights: LearningInsights
    focus_areas: list[str]
    celebration_worthy: list[str]


class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard."""
    daily_activity: list[DailyActivity]
    weekly_trends: list[WeeklyTrend]
    monthly_overview: MonthlyOverview
    domain_comparison: DomainComparison
    pattern_analytics: PatternAnalytics
    progress: ProgressMetrics
    ai_insights: Optional[str] = None
