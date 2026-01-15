"""
NeurOS 2.0 Reviews API Endpoints (SRS)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.services.srs_service import SRSService
from app.models.srs_review import SRSReview
from app.schemas.review import (
    ReviewItemCreate, ReviewSubmit, ReviewResult,
    ReviewQueue, ReviewItemWithData,
)
from app.dependencies import CurrentUser

router = APIRouter(prefix="/reviews", tags=["Reviews (SRS)"])


@router.get("/queue", response_model=ReviewQueue)
async def get_review_queue(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    """Get review queue with due items."""
    service = SRSService(db)
    items, stats = await service.get_review_queue(current_user.id, limit)
    
    # Get item data for each review
    items_with_data = []
    for review in items:
        item_data = await service.get_review_with_item_data(review)
        items_with_data.append(ReviewItemWithData(
            id=review.id,
            user_id=review.user_id,
            item_type=review.item_type,
            item_id=review.item_id,
            interval_days=review.interval_days,
            ease_factor=review.ease_factor,
            repetition_number=review.repetition_number,
            status=review.status,
            next_review_at=review.next_review_at,
            last_review_at=review.last_review_at,
            review_count=review.review_count,
            lapse_count=review.lapse_count,
            last_quality=review.last_quality,
            is_suspended=review.is_suspended,
            is_leech=review.is_leech,
            created_at=review.created_at,
            item_data=item_data,
        ))
    
    next_item = items_with_data[0] if items_with_data else None
    
    return ReviewQueue(
        stats=stats,
        items=items_with_data,
        next_item=next_item,
    )


@router.get("/next", response_model=ReviewItemWithData | None)
async def get_next_review(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get next item to review."""
    service = SRSService(db)
    review = await service.get_next_review_item(current_user.id)
    
    if not review:
        return None
    
    item_data = await service.get_review_with_item_data(review)
    
    return ReviewItemWithData(
        id=review.id,
        user_id=review.user_id,
        item_type=review.item_type,
        item_id=review.item_id,
        interval_days=review.interval_days,
        ease_factor=review.ease_factor,
        repetition_number=review.repetition_number,
        status=review.status,
        next_review_at=review.next_review_at,
        last_review_at=review.last_review_at,
        review_count=review.review_count,
        lapse_count=review.lapse_count,
        last_quality=review.last_quality,
        is_suspended=review.is_suspended,
        is_leech=review.is_leech,
        created_at=review.created_at,
        item_data=item_data,
    )


@router.post("/{review_id}/submit", response_model=ReviewResult)
async def submit_review(
    review_id: int,
    data: ReviewSubmit,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Submit a review with quality rating."""
    result = await db.execute(
        select(SRSReview)
        .where(and_(SRSReview.id == review_id, SRSReview.user_id == current_user.id))
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    service = SRSService(db)
    return await service.submit_review(review, data)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_review_item(
    data: ReviewItemCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new review item."""
    service = SRSService(db)
    review = await service.create_review_item(current_user.id, data)
    return {"id": review.id, "message": "Review item created"}


@router.post("/{review_id}/suspend")
async def suspend_review(
    review_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Suspend a review item."""
    result = await db.execute(
        select(SRSReview)
        .where(and_(SRSReview.id == review_id, SRSReview.user_id == current_user.id))
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    service = SRSService(db)
    await service.suspend_review(review)
    return {"message": "Review suspended"}


@router.post("/{review_id}/unsuspend")
async def unsuspend_review(
    review_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Unsuspend a review item."""
    result = await db.execute(
        select(SRSReview)
        .where(and_(SRSReview.id == review_id, SRSReview.user_id == current_user.id))
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    service = SRSService(db)
    await service.unsuspend_review(review)
    return {"message": "Review unsuspended"}
