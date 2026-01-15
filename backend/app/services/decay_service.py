"""
NeurOS 2.0 Decay Service

Business logic for knowledge decay tracking and alerts.
"""

from datetime import datetime, timezone, timedelta, date
from typing import Optional
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decay_tracking import DecayTracking, TrackableType
from app.models.entry import Entry
from app.models.pattern import Pattern
from app.models.knowledge_node import KnowledgeNode
from app.core.decay import DecayEngine, DecayStatus
from app.config import settings
from app.schemas.decay import (
    DecayOverview, DecayCriticalAlert, DecayDashboard,
    DecayStatusWithItem, HeatmapDay, PracticeHeatmap,
)


class DecayService:
    """Service for managing knowledge decay."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_decay_overview(self, user_id: int) -> DecayOverview:
        """Get overview of decay status across all tracked items."""
        result = await self.db.execute(
            select(DecayTracking)
            .where(DecayTracking.user_id == user_id)
        )
        items = result.scalars().all()
        
        # Update decay scores first
        await self._update_all_decay_scores(items)
        
        # Calculate counts by status
        fresh = stable = decaying = critical = forgotten = 0
        total_score = 0
        
        for item in items:
            total_score += item.decay_score
            if item.decay_score >= 80:
                fresh += 1
            elif item.decay_score >= 60:
                stable += 1
            elif item.decay_score >= 40:
                decaying += 1
            elif item.decay_score >= 20:
                critical += 1
            else:
                forgotten += 1
        
        # Count items due today
        today = date.today()
        due_today_result = await self.db.execute(
            select(func.count(DecayTracking.id))
            .where(
                and_(
                    DecayTracking.user_id == user_id,
                    DecayTracking.next_review_date <= today,
                )
            )
        )
        items_due_today = due_today_result.scalar() or 0
        
        avg_score = total_score / len(items) if items else 0
        
        return DecayOverview(
            total_tracked=len(items),
            fresh_count=fresh,
            stable_count=stable,
            decaying_count=decaying,
            critical_count=critical,
            forgotten_count=forgotten,
            average_decay_score=round(avg_score, 1),
            items_due_today=items_due_today,
        )
    
    async def _update_all_decay_scores(
        self,
        items: list[DecayTracking],
    ) -> None:
        """Update decay scores for all items."""
        now = datetime.now(timezone.utc)
        
        for item in items:
            if item.last_practiced_at:
                result = DecayEngine.calculate_decay_score(
                    last_practiced_at=item.last_practiced_at,
                    times_reviewed=item.times_reviewed,
                    initial_difficulty=item.initial_difficulty,
                    last_quality=item.last_quality or 4,
                    current_time=now,
                )
                item.decay_score = result.decay_score
                item.stability_factor = result.stability_factor
        
        await self.db.flush()
    
    async def get_critical_items(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[DecayCriticalAlert]:
        """Get items with critical decay levels."""
        result = await self.db.execute(
            select(DecayTracking)
            .where(
                and_(
                    DecayTracking.user_id == user_id,
                    DecayTracking.decay_score < settings.DECAY_WARNING_THRESHOLD,
                )
            )
            .order_by(DecayTracking.decay_score.asc())
            .limit(limit)
        )
        items = result.scalars().all()
        
        alerts = []
        now = datetime.now(timezone.utc)
        
        for item in items:
            # Get item name
            name = await self._get_item_name(item)
            
            days_since = 0
            if item.last_practiced_at:
                days_since = (now - item.last_practiced_at).days
            
            urgency = "critical" if item.decay_score < 30 else (
                "urgent" if item.decay_score < 40 else "warning"
            )
            
            alerts.append(DecayCriticalAlert(
                item_id=item.trackable_id,
                item_type=item.trackable_type,
                item_name=name,
                decay_score=item.decay_score,
                last_practiced_at=item.last_practiced_at,
                days_since_practice=days_since,
                urgency=urgency,
            ))
        
        return alerts
    
    async def _get_item_name(self, decay_item: DecayTracking) -> str:
        """Get the name of a tracked item."""
        if decay_item.trackable_type == TrackableType.ENTRY:
            result = await self.db.execute(
                select(Entry.title).where(Entry.id == decay_item.trackable_id)
            )
            title = result.scalar_one_or_none()
            return title or f"Entry #{decay_item.trackable_id}"
        
        elif decay_item.trackable_type == TrackableType.PATTERN:
            result = await self.db.execute(
                select(Pattern.name).where(Pattern.id == decay_item.trackable_id)
            )
            name = result.scalar_one_or_none()
            return name or f"Pattern #{decay_item.trackable_id}"
        
        elif decay_item.trackable_type == TrackableType.KNOWLEDGE_NODE:
            result = await self.db.execute(
                select(KnowledgeNode.name).where(KnowledgeNode.id == decay_item.trackable_id)
            )
            name = result.scalar_one_or_none()
            return name or f"Concept #{decay_item.trackable_id}"
        
        return f"Item #{decay_item.trackable_id}"
    
    async def get_practice_heatmap(
        self,
        user_id: int,
        days: int = 365,
    ) -> PracticeHeatmap:
        """Generate GitHub-style practice heatmap."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get all practice dates
        result = await self.db.execute(
            select(
                func.date(DecayTracking.last_practiced_at).label("practice_date"),
                func.count(DecayTracking.id).label("count"),
            )
            .where(
                and_(
                    DecayTracking.user_id == user_id,
                    DecayTracking.last_practiced_at >= start_date,
                )
            )
            .group_by(func.date(DecayTracking.last_practiced_at))
        )
        
        practice_counts = {row[0]: row[1] for row in result.all()}
        
        # Build heatmap
        heatmap_days = []
        current_date = start_date
        max_count = max(practice_counts.values()) if practice_counts else 1
        
        while current_date <= end_date:
            count = practice_counts.get(current_date, 0)
            # Calculate intensity (0-4 scale like GitHub)
            intensity = 0 if count == 0 else min(4, int((count / max_count) * 4) + 1)
            
            heatmap_days.append(HeatmapDay(
                date=current_date,
                count=count,
                intensity=intensity,
            ))
            current_date += timedelta(days=1)
        
        # Calculate streaks
        current_streak, longest_streak = self._calculate_streaks(heatmap_days)
        total_practiced = sum(1 for d in heatmap_days if d.count > 0)
        
        return PracticeHeatmap(
            days=heatmap_days,
            total_days_practiced=total_practiced,
            current_streak=current_streak,
            longest_streak=longest_streak,
            start_date=start_date,
            end_date=end_date,
        )
    
    def _calculate_streaks(self, days: list[HeatmapDay]) -> tuple[int, int]:
        """Calculate current and longest practice streaks."""
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Reverse to start from most recent
        for day in reversed(days):
            if day.count > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
                if temp_streak == (len(days) - days.index(day)):
                    current_streak = temp_streak
            else:
                if current_streak == 0 and temp_streak > 0:
                    # Check if we're still on current streak
                    pass
                temp_streak = 0
        
        # Simplified: count from today backwards
        current_streak = 0
        for day in reversed(days):
            if day.count > 0:
                current_streak += 1
            else:
                break
        
        return current_streak, longest_streak
    
    async def record_practice(
        self,
        user_id: int,
        trackable_type: TrackableType,
        trackable_id: int,
        quality: int = 4,
    ) -> DecayTracking:
        """Record a practice session, updating decay tracking."""
        result = await self.db.execute(
            select(DecayTracking)
            .where(
                and_(
                    DecayTracking.user_id == user_id,
                    DecayTracking.trackable_type == trackable_type,
                    DecayTracking.trackable_id == trackable_id,
                )
            )
        )
        decay = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if decay:
            decay.last_practiced_at = now
            decay.times_reviewed += 1
            decay.last_quality = quality
            decay.decay_score = 100  # Reset after practice
            
            # Calculate next review date based on stability
            days_until_review = max(1, int(decay.stability_factor * settings.DECAY_HALF_LIFE_DAYS * 0.5))
            decay.next_review_date = (now + timedelta(days=days_until_review)).date()
        else:
            decay = DecayTracking(
                user_id=user_id,
                trackable_type=trackable_type,
                trackable_id=trackable_id,
                decay_score=100,
                last_practiced_at=now,
                times_reviewed=1,
                last_quality=quality,
                next_review_date=(now + timedelta(days=1)).date(),
            )
            self.db.add(decay)
        
        await self.db.flush()
        await self.db.refresh(decay)
        
        return decay
