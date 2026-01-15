"""
NeurOS 2.0 Analytics Service
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.models.reflection import Reflection
from app.models.srs_review import SRSReview, ReviewStatus
from app.models.decay_tracking import DecayTracking


async def get_analytics_dashboard(
    db: AsyncSession,
    user_id: int,
    period_days: int = 30
) -> dict:
    """Get comprehensive analytics dashboard data."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=period_days)
    
    # Entry statistics
    entry_stats = await _get_entry_stats(db, user_id, period_start)
    
    # Review statistics
    review_stats = await _get_review_stats(db, user_id, period_start)
    
    # Learning velocity
    velocity = await _calculate_learning_velocity(db, user_id, period_days)
    
    # Retention metrics
    retention = await _calculate_retention_metrics(db, user_id)
    
    # Activity heatmap
    heatmap = await _get_activity_heatmap(db, user_id, period_days)
    
    # Domain distribution
    domains = await _get_domain_distribution(db, user_id)
    
    # Difficulty progression
    difficulty_progress = await _get_difficulty_progression(db, user_id, period_start)
    
    return {
        "period_days": period_days,
        "entry_stats": entry_stats,
        "review_stats": review_stats,
        "learning_velocity": velocity,
        "retention_metrics": retention,
        "activity_heatmap": heatmap,
        "domain_distribution": domains,
        "difficulty_progression": difficulty_progress,
        "generated_at": now.isoformat(),
    }


async def _get_entry_stats(
    db: AsyncSession,
    user_id: int,
    period_start: datetime
) -> dict:
    """Get entry creation statistics."""
    # Total entries
    total_result = await db.execute(
        select(func.count(Entry.id)).where(Entry.user_id == user_id)
    )
    total = total_result.scalar() or 0
    
    # Period entries
    period_result = await db.execute(
        select(func.count(Entry.id)).where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= period_start
            )
        )
    )
    period_count = period_result.scalar() or 0
    
    # By type
    type_result = await db.execute(
        select(Entry.entry_type, func.count(Entry.id))
        .where(Entry.user_id == user_id)
        .group_by(Entry.entry_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}
    
    # Completion rate
    completed_result = await db.execute(
        select(func.count(Entry.id)).where(
            and_(
                Entry.user_id == user_id,
                Entry.is_completed == True
            )
        )
    )
    completed = completed_result.scalar() or 0
    
    return {
        "total": total,
        "period_count": period_count,
        "by_type": by_type,
        "completed": completed,
        "completion_rate": completed / total if total > 0 else 0,
    }


async def _get_review_stats(
    db: AsyncSession,
    user_id: int,
    period_start: datetime
) -> dict:
    """Get review statistics."""
    # Total reviews
    total_result = await db.execute(
        select(func.count(SRSReview.id)).where(SRSReview.user_id == user_id)
    )
    total = total_result.scalar() or 0
    
    # Period reviews (completed)
    period_result = await db.execute(
        select(func.count(SRSReview.id)).where(
            and_(
                SRSReview.user_id == user_id,
                SRSReview.last_reviewed >= period_start
            )
        )
    )
    period_count = period_result.scalar() or 0
    
    # By status
    status_result = await db.execute(
        select(SRSReview.status, func.count(SRSReview.id))
        .where(SRSReview.user_id == user_id)
        .group_by(SRSReview.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}
    
    # Average ease factor
    ease_result = await db.execute(
        select(func.avg(SRSReview.ease_factor)).where(SRSReview.user_id == user_id)
    )
    avg_ease = ease_result.scalar() or 2.5
    
    return {
        "total": total,
        "period_count": period_count,
        "by_status": by_status,
        "average_ease_factor": round(float(avg_ease), 2),
    }


async def _calculate_learning_velocity(
    db: AsyncSession,
    user_id: int,
    period_days: int
) -> dict:
    """Calculate learning velocity metrics."""
    now = datetime.utcnow()
    
    # Daily averages for the period
    daily_entries = []
    for i in range(period_days):
        day_start = now - timedelta(days=i+1)
        day_end = now - timedelta(days=i)
        
        result = await db.execute(
            select(func.count(Entry.id)).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= day_start,
                    Entry.created_at < day_end
                )
            )
        )
        daily_entries.append(result.scalar() or 0)
    
    avg_daily = sum(daily_entries) / len(daily_entries) if daily_entries else 0
    
    # Trend (comparing last 7 days vs previous 7 days)
    recent = sum(daily_entries[:7]) if len(daily_entries) >= 7 else sum(daily_entries)
    previous = sum(daily_entries[7:14]) if len(daily_entries) >= 14 else 0
    
    if previous > 0:
        trend_percent = ((recent - previous) / previous) * 100
    else:
        trend_percent = 100 if recent > 0 else 0
    
    return {
        "daily_average": round(avg_daily, 2),
        "recent_7_days": recent,
        "previous_7_days": previous,
        "trend_percent": round(trend_percent, 1),
        "trend_direction": "up" if trend_percent > 0 else "down" if trend_percent < 0 else "stable",
    }


async def _calculate_retention_metrics(
    db: AsyncSession,
    user_id: int
) -> dict:
    """Calculate retention metrics from decay tracking."""
    # Average retention
    result = await db.execute(
        select(func.avg(DecayTracking.current_retention)).where(
            DecayTracking.user_id == user_id
        )
    )
    avg_retention = result.scalar() or 0
    
    # Items at risk (below 50%)
    risk_result = await db.execute(
        select(func.count(DecayTracking.id)).where(
            and_(
                DecayTracking.user_id == user_id,
                DecayTracking.current_retention < 0.5
            )
        )
    )
    at_risk = risk_result.scalar() or 0
    
    # Items mastered (above 90%)
    mastered_result = await db.execute(
        select(func.count(DecayTracking.id)).where(
            and_(
                DecayTracking.user_id == user_id,
                DecayTracking.current_retention >= 0.9
            )
        )
    )
    mastered = mastered_result.scalar() or 0
    
    return {
        "average_retention": round(float(avg_retention), 2),
        "items_at_risk": at_risk,
        "items_mastered": mastered,
    }


async def _get_activity_heatmap(
    db: AsyncSession,
    user_id: int,
    period_days: int
) -> list[dict]:
    """Get activity heatmap data."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=period_days)
    
    result = await db.execute(
        select(
            func.date(Entry.created_at).label('date'),
            func.count(Entry.id).label('count')
        )
        .where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= period_start
            )
        )
        .group_by(func.date(Entry.created_at))
    )
    
    return [
        {"date": str(row.date), "count": row.count}
        for row in result.all()
    ]


async def _get_domain_distribution(
    db: AsyncSession,
    user_id: int
) -> list[dict]:
    """Get distribution of entries by domain."""
    result = await db.execute(
        select(Entry.domain, func.count(Entry.id).label('count'))
        .where(Entry.user_id == user_id)
        .group_by(Entry.domain)
        .order_by(func.count(Entry.id).desc())
        .limit(10)
    )
    
    return [
        {"domain": row.domain, "count": row.count}
        for row in result.all()
    ]


async def _get_difficulty_progression(
    db: AsyncSession,
    user_id: int,
    period_start: datetime
) -> dict:
    """Get difficulty level progression over time."""
    result = await db.execute(
        select(Entry.difficulty, func.count(Entry.id))
        .where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= period_start
            )
        )
        .group_by(Entry.difficulty)
    )
    
    return {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in result.all()}
