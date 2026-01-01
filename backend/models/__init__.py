"""
Models package initialization.

WHY: Clean model imports for the rest of the application.
All models are importable from `models` directly.
"""

from models.entry import Entry, EntryType
from models.pattern import Pattern, EntryPattern
from models.reflection import Reflection
from models.analytics import BlockerAnalytics, RevisionHistory, DailyStats
from models.recommendation import (
    Recommendation, RecommendationType, 
    RecommendationPriority, RecommendationDomain
)
from models.learning_plan import (
    LearningPlan, PlanMilestone, WeeklySchedule, DailyTask,
    PlanType, PlanStatus, MilestoneStatus
)

__all__ = [
    "Entry",
    "EntryType", 
    "Pattern",
    "EntryPattern",
    "Reflection",
    "BlockerAnalytics",
    "RevisionHistory",
    "DailyStats",
    "Recommendation",
    "RecommendationType",
    "RecommendationPriority",
    "RecommendationDomain",
    "LearningPlan",
    "PlanMilestone",
    "WeeklySchedule",
    "DailyTask",
    "PlanType",
    "PlanStatus",
    "MilestoneStatus",
]
