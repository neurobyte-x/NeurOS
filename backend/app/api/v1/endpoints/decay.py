"""
NeurOS 2.0 Decay API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.decay_service import DecayService
from app.models.decay_tracking import TrackableType
from app.schemas.decay import (
    DecayOverview, DecayCriticalAlert, DecayDashboard,
    PracticeHeatmap, DecayStatusResponse,
)
from app.dependencies import CurrentUser

router = APIRouter(prefix="/decay", tags=["Decay Tracking"])


@router.get("/overview", response_model=DecayOverview)
async def get_decay_overview(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get overview of decay status across all items."""
    service = DecayService(db)
    return await service.get_decay_overview(current_user.id)


@router.get("/critical", response_model=list[DecayCriticalAlert])
async def get_critical_items(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """Get items with critical decay levels."""
    service = DecayService(db)
    return await service.get_critical_items(current_user.id, limit)


@router.get("/heatmap", response_model=PracticeHeatmap)
async def get_practice_heatmap(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    days: int = Query(365, ge=30, le=730),
):
    """Get GitHub-style practice heatmap."""
    service = DecayService(db)
    return await service.get_practice_heatmap(current_user.id, days)


@router.post("/practice", response_model=DecayStatusResponse)
async def record_practice(
    trackable_type: TrackableType,
    trackable_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    quality: int = Query(4, ge=0, le=5),
):
    """Record a practice session."""
    service = DecayService(db)
    decay = await service.record_practice(
        current_user.id, trackable_type, trackable_id, quality
    )
    return decay
