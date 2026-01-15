"""
NeurOS 2.0 Entry Service

Business logic for learning entries and reflections.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entry import Entry, EntryType
from app.models.reflection import Reflection
from app.models.decay_tracking import DecayTracking, TrackableType
from app.models.srs_review import SRSReview, ReviewItemType, ReviewStatus
from app.schemas.entry import (
    EntryCreate, EntryUpdate, EntryFilter, ReflectionCreate
)


class EntryService:
    """Service for managing learning entries."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_entry(self, user_id: int, data: EntryCreate) -> Entry:
        """Create a new learning entry."""
        entry = Entry(
            user_id=user_id,
            title=data.title,
            entry_type=data.entry_type,
            problem_url=data.problem_url,
            tags=data.tags or [],
            difficulty=data.difficulty,
            time_spent_minutes=data.time_spent_minutes,
        )
        
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        
        return entry
    
    async def get_entry(self, entry_id: int, user_id: int) -> Optional[Entry]:
        """Get entry by ID for a specific user."""
        result = await self.db.execute(
            select(Entry)
            .options(selectinload(Entry.reflection))
            .options(selectinload(Entry.patterns))
            .where(and_(Entry.id == entry_id, Entry.user_id == user_id))
        )
        return result.scalar_one_or_none()
    
    async def get_entries(
        self,
        user_id: int,
        filters: Optional[EntryFilter] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Entry], int]:
        """Get paginated list of entries with filters."""
        query = (
            select(Entry)
            .options(selectinload(Entry.reflection))
            .where(Entry.user_id == user_id)
        )
        
        # Apply filters
        if filters:
            if filters.entry_type:
                query = query.where(Entry.entry_type == filters.entry_type)
            if filters.is_completed is not None:
                query = query.where(Entry.is_completed == filters.is_completed)
            if filters.difficulty:
                query = query.where(Entry.difficulty == filters.difficulty)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        Entry.title.ilike(search_term),
                        Entry.tags.any(filters.search),
                    )
                )
            if filters.created_after:
                query = query.where(Entry.created_at >= filters.created_after)
            if filters.created_before:
                query = query.where(Entry.created_at <= filters.created_before)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        
        # Apply pagination
        query = (
            query
            .order_by(Entry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        
        return entries, total
    
    async def update_entry(
        self,
        entry: Entry,
        data: EntryUpdate,
    ) -> Entry:
        """Update an entry."""
        update_dict = data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(entry, field, value)
        
        entry.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(entry)
        
        return entry
    
    async def delete_entry(self, entry: Entry) -> None:
        """Delete an entry."""
        await self.db.delete(entry)
        await self.db.flush()
    
    async def add_reflection(
        self,
        entry: Entry,
        data: ReflectionCreate,
    ) -> Entry:
        """Add reflection to entry, marking it as completed."""
        reflection = Reflection(
            entry_id=entry.id,
            problem_context=data.problem_context,
            initial_blocker=data.initial_blocker,
            trigger_signal=data.trigger_signal,
            key_pattern=data.key_pattern,
            mistakes_edge_cases=data.mistakes_edge_cases,
            what_i_would_do_differently=data.what_i_would_do_differently,
            related_concepts=data.related_concepts,
            confidence_level=data.confidence_level,
        )
        
        self.db.add(reflection)
        
        # Mark entry as completed
        entry.is_completed = True
        entry.completed_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        
        # Create decay tracking for completed entry
        await self._create_decay_tracking(entry)
        
        # Create SRS review item
        await self._create_srs_review(entry)
        
        await self.db.refresh(entry)
        
        return entry
    
    async def _create_decay_tracking(self, entry: Entry) -> None:
        """Create decay tracking for a completed entry."""
        decay_tracking = DecayTracking(
            user_id=entry.user_id,
            trackable_type=TrackableType.ENTRY,
            trackable_id=entry.id,
            decay_score=100,
            last_practiced_at=datetime.now(timezone.utc),
            initial_difficulty=entry.difficulty_score,
        )
        self.db.add(decay_tracking)
    
    async def _create_srs_review(self, entry: Entry) -> None:
        """Create SRS review item for a completed entry."""
        srs_review = SRSReview(
            user_id=entry.user_id,
            item_type=ReviewItemType.ENTRY,
            item_id=entry.id,
            next_review_at=datetime.now(timezone.utc),  # Due immediately for first review
            status=ReviewStatus.LEARNING,
        )
        self.db.add(srs_review)
    
    async def get_entry_count_by_type(self, user_id: int) -> dict[str, int]:
        """Get count of entries by type."""
        result = await self.db.execute(
            select(Entry.entry_type, func.count(Entry.id))
            .where(Entry.user_id == user_id)
            .group_by(Entry.entry_type)
        )
        
        return {row[0].value: row[1] for row in result.all()}
    
    async def get_recent_entries(
        self,
        user_id: int,
        limit: int = 5,
    ) -> list[Entry]:
        """Get most recent entries."""
        result = await self.db.execute(
            select(Entry)
            .options(selectinload(Entry.reflection))
            .where(Entry.user_id == user_id)
            .order_by(Entry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
