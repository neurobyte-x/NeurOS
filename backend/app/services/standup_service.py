"""
NeurOS 2.0 Standup Service

Business logic for daily standup / morning plan generation.
"""

from datetime import datetime, timezone, timedelta, date
from typing import Optional
import random

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.srs_review import SRSReview, ReviewItemType, ReviewStatus
from app.models.decay_tracking import DecayTracking
from app.models.entry import Entry, EntryType
from app.models.pattern import Pattern
from app.services.srs_service import SRSService
from app.services.decay_service import DecayService
from app.config import settings
from app.schemas.standup import (
    DailyPlan, DailyPlanStats, SuggestedChallenge,
    WeakAreaAlert, WeeklyReport,
)
from app.schemas.review import ReviewItemWithData


class StandupService:
    """Service for generating daily standup plans."""
    
    GREETINGS = [
        "Good morning! Ready to strengthen your knowledge?",
        "Welcome back! Let's prevent some skill decay today.",
        "Hello! Time to level up your expertise.",
        "Hey there! Your brain is ready for some exercise.",
        "Good to see you! Let's make today count.",
    ]
    
    MOTIVATIONS = [
        "Every review strengthens your neural pathways. Keep going!",
        "Consistency beats intensity. You're doing great!",
        "Small daily progress leads to massive long-term gains.",
        "Your future self will thank you for reviewing today.",
        "The best time to review was yesterday. The next best time is now.",
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.srs_service = SRSService(db)
        self.decay_service = DecayService(db)
    
    async def generate_daily_plan(
        self,
        user: User,
    ) -> DailyPlan:
        """Generate personalized daily plan."""
        now = datetime.now(timezone.utc)
        today = now.date()
        
        # Get review queue
        due_items, queue_stats = await self.srs_service.get_review_queue(
            user.id, limit=50
        )
        
        # Get critical decay items
        critical_items = await self.decay_service.get_critical_items(
            user.id, limit=5
        )
        
        # Calculate stats
        stats = await self._calculate_stats(user, queue_stats)
        
        # Get high priority reviews (most overdue or critical decay)
        high_priority = await self._get_high_priority_reviews(user.id, limit=5)
        
        # Get scheduled reviews for today
        scheduled = await self._get_scheduled_reviews(user.id, limit=10)
        
        # Get weak areas
        weak_areas = await self._identify_weak_areas(user.id)
        
        # Generate suggested challenge
        suggested_challenge = await self._suggest_challenge(user.id)
        
        # Check for achievements
        achievement = await self._check_achievements(user)
        
        return DailyPlan(
            date=today,
            greeting=random.choice(self.GREETINGS),
            stats=stats,
            high_priority_reviews=high_priority,
            scheduled_reviews=scheduled,
            suggested_challenge=suggested_challenge,
            weak_areas=weak_areas,
            critical_decay_items=critical_items,
            motivation_message=random.choice(self.MOTIVATIONS),
            achievement_unlocked=achievement,
        )
    
    async def _calculate_stats(
        self,
        user: User,
        queue_stats,
    ) -> DailyPlanStats:
        """Calculate daily stats."""
        # Get current streak from heatmap
        heatmap = await self.decay_service.get_practice_heatmap(user.id, days=30)
        
        # Count reviews completed today
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        reviews_today_result = await self.db.execute(
            select(func.count(SRSReview.id))
            .where(
                and_(
                    SRSReview.user_id == user.id,
                    SRSReview.last_review_at >= today_start,
                )
            )
        )
        reviews_completed = reviews_today_result.scalar() or 0
        
        goal_progress = (reviews_completed / user.daily_review_goal * 100) if user.daily_review_goal > 0 else 0
        
        return DailyPlanStats(
            current_streak=heatmap.current_streak,
            total_reviews_pending=queue_stats.due_today,
            estimated_time_minutes=queue_stats.estimated_time_minutes,
            reviews_completed_today=reviews_completed,
            daily_goal=user.daily_review_goal,
            goal_progress_percent=min(100, round(goal_progress, 1)),
        )
    
    async def _get_high_priority_reviews(
        self,
        user_id: int,
        limit: int = 5,
    ) -> list[ReviewItemWithData]:
        """Get highest priority review items."""
        # Get items with critical decay or very overdue
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
            .limit(limit)
        )
        reviews = result.scalars().all()
        
        items = []
        for review in reviews:
            item_data = await self.srs_service.get_review_with_item_data(review)
            items.append(ReviewItemWithData(
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
                is_due=review.is_due,
                is_overdue=review.is_overdue,
                item_data=item_data,
            ))
        
        return items
    
    async def _get_scheduled_reviews(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[ReviewItemWithData]:
        """Get scheduled reviews for today."""
        # Similar to high priority but includes all due today
        return await self._get_high_priority_reviews(user_id, limit)
    
    async def _identify_weak_areas(
        self,
        user_id: int,
    ) -> list[WeakAreaAlert]:
        """Identify weak areas based on decay and struggle patterns."""
        weak_areas = []
        
        # Find patterns/concepts with low decay scores
        result = await self.db.execute(
            select(DecayTracking)
            .where(
                and_(
                    DecayTracking.user_id == user_id,
                    DecayTracking.decay_score < settings.DECAY_WARNING_THRESHOLD,
                )
            )
            .order_by(DecayTracking.decay_score.asc())
            .limit(3)
        )
        
        for decay_item in result.scalars().all():
            name = await self.decay_service._get_item_name(decay_item)
            
            weak_areas.append(WeakAreaAlert(
                domain=decay_item.trackable_type.value,
                pattern_or_concept=name,
                decay_score=decay_item.decay_score,
                times_struggled=decay_item.times_reviewed,
                last_seen=decay_item.last_practiced_at,
                suggestion=f"Review '{name}' to strengthen your understanding",
            ))
        
        return weak_areas
    
    async def _suggest_challenge(
        self,
        user_id: int,
    ) -> Optional[SuggestedChallenge]:
        """Suggest a new learning challenge based on user's profile."""
        # Find domain with good progress to suggest advancement
        result = await self.db.execute(
            select(Entry.entry_type, func.count(Entry.id).label("count"))
            .where(
                and_(
                    Entry.user_id == user_id,
                    Entry.is_completed == True,
                )
            )
            .group_by(Entry.entry_type)
            .order_by(func.count(Entry.id).desc())
        )
        
        domain_counts = {row[0]: row[1] for row in result.all()}
        
        if not domain_counts:
            return SuggestedChallenge(
                entry_type="concept",
                title="Start Your Learning Journey",
                description="Create your first learning entry to begin tracking your progress",
                estimated_time_minutes=30,
                reason="New user - time to build your knowledge base",
                tags=["getting-started"],
            )
        
        # Suggest based on strongest domain
        strongest_domain = max(domain_counts, key=domain_counts.get)
        
        suggestions = {
            EntryType.DSA: SuggestedChallenge(
                entry_type="dsa",
                title="Try a Medium-Hard Algorithm Problem",
                description="Challenge yourself with a problem that combines multiple concepts",
                estimated_time_minutes=45,
                reason=f"You've completed {domain_counts[strongest_domain]} DSA entries - time to level up!",
                tags=["algorithms", "challenge"],
            ),
            EntryType.BACKEND: SuggestedChallenge(
                entry_type="backend",
                title="Build a New API Endpoint",
                description="Practice designing and implementing a RESTful endpoint",
                estimated_time_minutes=60,
                reason="Strengthen your backend skills with hands-on practice",
                tags=["api", "backend", "practice"],
            ),
            EntryType.AI_ML: SuggestedChallenge(
                entry_type="ai_ml",
                title="Experiment with a New Model Architecture",
                description="Try implementing or fine-tuning a model you haven't used before",
                estimated_time_minutes=90,
                reason="Expand your ML toolkit with new techniques",
                tags=["machine-learning", "experiment"],
            ),
        }
        
        return suggestions.get(strongest_domain, SuggestedChallenge(
            entry_type="concept",
            title="Explore a New Concept",
            description="Pick a topic you're curious about and dive deep",
            estimated_time_minutes=45,
            reason="Continuous learning keeps your skills sharp",
            tags=["learning", "exploration"],
        ))
    
    async def _check_achievements(self, user: User) -> Optional[str]:
        """Check for newly unlocked achievements."""
        # Simple achievement checks
        heatmap = await self.decay_service.get_practice_heatmap(user.id, days=30)
        
        if heatmap.current_streak == 7:
            return "🔥 7-Day Streak! You're on fire!"
        elif heatmap.current_streak == 30:
            return "🏆 30-Day Streak! Incredible dedication!"
        
        # Check total entries
        entry_count = await self.db.execute(
            select(func.count(Entry.id))
            .where(
                and_(
                    Entry.user_id == user.id,
                    Entry.is_completed == True,
                )
            )
        )
        total = entry_count.scalar() or 0
        
        milestones = {10: "📚 10 Entries!", 50: "📖 50 Entries!", 100: "🎓 100 Entries!"}
        
        return milestones.get(total)
