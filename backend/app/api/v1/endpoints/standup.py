"""
NeurOS 2.0 Standup API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.standup_service import StandupService
from app.schemas.standup import DailyPlan
from app.dependencies import CurrentUser

router = APIRouter(prefix="/standup", tags=["Daily Standup"])


@router.get("/today", response_model=DailyPlan)
async def get_daily_plan(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get today's personalized learning plan."""
    service = StandupService(db)
    return await service.generate_daily_plan(current_user)
