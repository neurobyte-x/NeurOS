"""
NeurOS 2.0 SRS Service

Spaced Repetition System business logic.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.srs_review import SRSReview, ReviewItemType, ReviewStatus
from app.models.entry import Entry
from app.models.pattern import Pattern
from app.models.decay_tracking import DecayTracking, TrackableType
from app.core.srs import SRSEngine, RecallQuality
from app.schemas.review import (
    ReviewItemCreate, ReviewSubmit, ReviewResult,
    ReviewQueueStats, ReviewItemWithData,
)


class SRSService:
    """Service for spaced repetition system."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_review_queue(
        self,
        user_id: int,
        limit: int = 20,
    ) -> tuple[list[SRSReview], ReviewQueueStats]:
        """Get review queue with items due for review."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get due items
        result = await self.db.execute(
            select(SRSReview)
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.is_suspended == False,
                    SRSReview.next_review_at <= now,
                )
            )
            .order_by(SRSReview.next_review_at.asc())
            .limit(limit)
        )
        due_items = list(result.scalars().all())
        
        # Calculate stats
        stats = await self._calculate_queue_stats(user_id, now, today_start, today_end)
        
        return due_items, stats
    
    async def _calculate_queue_stats(
        self,
        user_id: int,
        now: datetime,
        today_start: datetime,
        today_end: datetime,
    ) -> ReviewQueueStats:
        """Calculate review queue statistics."""
        # Due now
        due_now_count = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.is_suspended == False,
                    SRSReview.next_review_at <= now,
                )
            )
        )
        due_now = due_now_count.scalar() or 0
        
        # Due today
        due_today_count = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.is_suspended == False,
                    SRSReview.next_review_at <= today_end,
                )
            )
        )
        due_today = due_today_count.scalar() or 0
        
        # Learning count
        learning_count_result = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.status == ReviewStatus.LEARNING,
                )
            )
        )
        learning_count = learning_count_result.scalar() or 0
        
        # Review count
        review_count_result = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.status == ReviewStatus.REVIEW,
                )
            )
        )
        review_count = review_count_result.scalar() or 0
        
        # Overdue count
        overdue_count_result = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.is_suspended == False,
                    SRSReview.next_review_at < today_start,
                )
            )
        )
        overdue_count = overdue_count_result.scalar() or 0
        
        # Estimate time (2 minutes per item)
        estimated_time = due_today * 2
        
        return ReviewQueueStats(
            due_now=due_now,
            due_today=due_today,
            learning_count=learning_count,
            review_count=review_count,
            overdue_count=overdue_count,
            estimated_time_minutes=estimated_time,
        )
    
    async def get_next_review_item(
        self,
        user_id: int,
    ) -> Optional[SRSReview]:
        """Get next item to review."""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(SRSReview)
            .where(
                and_(
                    SRSReview.user_id == user_id,
                    SRSReview.is_suspended == False,
                    SRSReview.next_review_at <= now,
                )
            )
            .order_by(SRSReview.next_review_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def submit_review(
        self,
        review: SRSReview,
        data: ReviewSubmit,
    ) -> ReviewResult:
        """Submit a review and update SRS state."""
        # Calculate next interval using SRS algorithm
        srs_result = SRSEngine.calculate_next_review(
            quality=data.quality,
            current_interval=review.interval_days,
            ease_factor=review.ease_factor,
            repetition_number=review.repetition_number,
            is_graduated=review.is_graduated,
        )
        
        # Update review record
        review.interval_days = srs_result.next_interval_days
        review.ease_factor = srs_result.new_ease_factor
        review.next_review_at = srs_result.next_review_date
        review.last_review_at = datetime.now(timezone.utc)
        review.review_count += 1
        review.repetition_number = srs_result.repetition_number
        review.last_quality = data.quality
        
        if data.time_taken_seconds:
            review.total_time_seconds += data.time_taken_seconds
        
        # Update status
        if srs_result.is_graduated:
            review.status = ReviewStatus.REVIEW
        
        # Track lapses
        if data.quality < 3:
            review.lapse_count += 1
            if review.lapse_count >= 8:  # Leech threshold
                review.is_leech = True
        
        await self.db.flush()
        
        # Update decay tracking
        await self._update_decay_after_review(review, data.quality)
        
        # Generate feedback message
        message = self._generate_feedback_message(data.quality, srs_result.next_interval_days)
        
        return ReviewResult(
            review_id=review.id,
            new_interval_days=srs_result.next_interval_days,
            new_ease_factor=srs_result.new_ease_factor,
            next_review_at=srs_result.next_review_date,
            is_graduated=srs_result.is_graduated,
            repetition_number=srs_result.repetition_number,
            message=message,
        )
    
    async def _update_decay_after_review(
        self,
        review: SRSReview,
        quality: int,
    ) -> None:
        """Update decay tracking after a review."""
        trackable_type = TrackableType(review.item_type.value)
        
        result = await self.db.execute(
            select(DecayTracking)
            .where(
                and_(
                    DecayTracking.user_id == review.user_id,
                    DecayTracking.trackable_type == trackable_type,
                    DecayTracking.trackable_id == review.item_id,
                )
            )
        )
        decay = result.scalar_one_or_none()
        
        if decay:
            decay.last_practiced_at = datetime.now(timezone.utc)
            decay.times_reviewed += 1
            decay.last_quality = quality
            decay.decay_score = 100  # Reset after practice
            decay.next_review_date = review.next_review_at.date()
            await self.db.flush()
    
    def _generate_feedback_message(self, quality: int, next_interval: int) -> str:
        """Generate feedback message based on quality."""
        if quality >= 5:
            return f"Perfect! See you in {next_interval} days."
        elif quality >= 4:
            return f"Good recall! Next review in {next_interval} days."
        elif quality >= 3:
            return f"Correct, but needs practice. See you in {next_interval} days."
        elif quality >= 2:
            return "Keep practicing - you'll get it!"
        else:
            return "No worries, we'll review this again soon."
    
    async def create_review_item(
        self,
        user_id: int,
        data: ReviewItemCreate,
    ) -> SRSReview:
        """Create a new review item."""
        review = SRSReview(
            user_id=user_id,
            item_type=data.item_type,
            item_id=data.item_id,
            next_review_at=datetime.now(timezone.utc),
            status=ReviewStatus.LEARNING,
        )
        
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        
        return review
    
    async def suspend_review(self, review: SRSReview) -> None:
        """Suspend a review item."""
        review.is_suspended = True
        await self.db.flush()
    
    async def unsuspend_review(self, review: SRSReview) -> None:
        """Unsuspend a review item."""
        review.is_suspended = False
        await self.db.flush()
    
    async def get_review_with_item_data(
        self,
        review: SRSReview,
    ) -> dict[str, Any]:
        """Get review with its associated item data."""
        item_data = {}
        
        if review.item_type == ReviewItemType.ENTRY:
            result = await self.db.execute(
                select(Entry)
                .options(selectinload(Entry.reflection))
                .where(Entry.id == review.item_id)
            )
            entry = result.scalar_one_or_none()
            if entry:
                item_data = {
                    "id": entry.id,
                    "title": entry.title,
                    "entry_type": entry.entry_type.value,
                    "reflection": {
                        "problem_context": entry.reflection.problem_context if entry.reflection else None,
                        "key_pattern": entry.reflection.key_pattern if entry.reflection else None,
                    } if entry.reflection else None,
                }
        
        elif review.item_type == ReviewItemType.PATTERN:
            result = await self.db.execute(
                select(Pattern)
                .options(selectinload(Pattern.templates))
                .where(Pattern.id == review.item_id)
            )
            pattern = result.scalar_one_or_none()
            if pattern:
                item_data = {
                    "id": pattern.id,
                    "name": pattern.name,
                    "description": pattern.description,
                    "templates": [
                        {"language": t.language.value, "template_code": t.template_code}
                        for t in pattern.templates
                    ],
                }
        
        return item_data
