"""
Analytics routes - tracking and insights API.

WHY: Data-driven improvement requires visibility.
These endpoints provide progress tracking and insights.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.analytics import RevisionCreate, RevisionResponse
from services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/daily")
def get_daily_stats(
    date: Optional[str] = None,  # ISO format: 2024-01-15
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific day.
    
    WHY: Daily dashboard view of learning activity.
    """
    service = AnalyticsService(db)
    
    date_obj = None
    if date:
        try:
            date_obj = datetime.fromisoformat(date)
        except ValueError:
            pass
    
    return service.get_daily_stats(date_obj)


@router.get("/weekly")
def get_weekly_summary(
    weeks_back: int = Query(1, ge=1, le=52),
    db: Session = Depends(get_db)
):
    """
    Get weekly summary with daily breakdown.
    
    WHY: Weekly review helps identify trends and patterns.
    """
    service = AnalyticsService(db)
    return service.get_weekly_summary(weeks_back)


@router.get("/insights")
def get_progress_insights(db: Session = Depends(get_db)):
    """
    Get learning progress insights.
    
    WHY: High-level analysis of strengths, weaknesses,
    and improvement opportunities.
    """
    service = AnalyticsService(db)
    return service.get_progress_insights()


@router.get("/blockers")
def get_blocker_analysis(db: Session = Depends(get_db)):
    """
    Analyze blocker patterns.
    
    WHY: Understand systematic blockers to target improvement.
    """
    service = AnalyticsService(db)
    return service.get_blocker_analysis()


@router.get("/revision-queue")
def get_revision_queue(db: Session = Depends(get_db)):
    """
    Get items due for revision.
    
    WHY: Spaced repetition queue for daily review session.
    """
    service = AnalyticsService(db)
    return service.get_revision_queue()


@router.post("/revision", response_model=RevisionResponse)
def record_revision(
    revision_data: RevisionCreate,
    db: Session = Depends(get_db)
):
    """
    Record a revision session.
    
    WHY: Track when and how well you reviewed something.
    Updates spaced repetition schedule.
    """
    service = AnalyticsService(db)
    revision = service.record_revision(
        entry_id=revision_data.entry_id,
        pattern_id=revision_data.pattern_id,
        revision_type=revision_data.revision_type,
        recall_quality=revision_data.recall_quality,
        confidence_after=revision_data.confidence_after,
        revision_notes=revision_data.revision_notes,
        time_spent_minutes=revision_data.time_spent_minutes,
    )
    return revision


@router.get("/streak")
def get_current_streak(db: Session = Depends(get_db)):
    """
    Get current learning streak.
    
    WHY: Gamification element - consecutive days with entries.
    """
    service = AnalyticsService(db)
    streak = service._calculate_streak()
    return {
        "streak_days": streak,
        "message": f"🔥 {streak} day streak!" if streak > 0 else "Start your streak today!"
    }
