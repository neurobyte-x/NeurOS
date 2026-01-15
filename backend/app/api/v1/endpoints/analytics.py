"""
NeurOS 2.0 Analytics API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_analytics_dashboard(
    period_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive analytics dashboard."""
    return await analytics_service.get_analytics_dashboard(
        db=db,
        user_id=current_user.id,
        period_days=period_days,
    )


@router.get("/summary")
async def get_quick_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a quick summary of key metrics (last 7 days)."""
    dashboard = await analytics_service.get_analytics_dashboard(
        db=db,
        user_id=current_user.id,
        period_days=7,
    )
    
    return {
        "entries_this_week": dashboard["entry_stats"]["period_count"],
        "reviews_this_week": dashboard["review_stats"]["period_count"],
        "average_retention": dashboard["retention_metrics"]["average_retention"],
        "items_at_risk": dashboard["retention_metrics"]["items_at_risk"],
        "trend": dashboard["learning_velocity"]["trend_direction"],
    }
