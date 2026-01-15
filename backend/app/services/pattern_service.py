"""
NeurOS 2.0 Pattern Service

Business logic for thinking patterns.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pattern import Pattern, entry_patterns
from app.models.pattern_template import PatternTemplate
from app.models.entry import Entry
from app.schemas.pattern import (
    PatternCreate, PatternUpdate, PatternTemplateCreate
)


class PatternService:
    """Service for managing thinking patterns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_pattern(self, user_id: int, data: PatternCreate) -> Pattern:
        """Create a new thinking pattern."""
        pattern = Pattern(
            user_id=user_id,
            name=data.name,
            description=data.description,
            domain=data.domain,
            when_to_use=data.when_to_use,
            common_triggers=data.common_triggers,
            common_mistakes=data.common_mistakes,
        )
        
        self.db.add(pattern)
        await self.db.flush()
        await self.db.refresh(pattern)
        
        return pattern
    
    async def get_pattern(self, pattern_id: int, user_id: int) -> Optional[Pattern]:
        """Get pattern by ID."""
        result = await self.db.execute(
            select(Pattern)
            .options(selectinload(Pattern.templates))
            .options(selectinload(Pattern.entries))
            .where(and_(Pattern.id == pattern_id, Pattern.user_id == user_id))
        )
        return result.scalar_one_or_none()
    
    async def get_patterns(
        self,
        user_id: int,
        domain: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Pattern], int]:
        """Get paginated list of patterns."""
        query = (
            select(Pattern)
            .options(selectinload(Pattern.templates))
            .where(Pattern.user_id == user_id)
        )
        
        if domain:
            query = query.where(Pattern.domain == domain)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        
        # Apply pagination and ordering
        query = (
            query
            .order_by(Pattern.usage_count.desc(), Pattern.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.db.execute(query)
        patterns = list(result.scalars().all())
        
        return patterns, total
    
    async def update_pattern(self, pattern: Pattern, data: PatternUpdate) -> Pattern:
        """Update a pattern."""
        update_dict = data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(pattern, field, value)
        
        pattern.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(pattern)
        
        return pattern
    
    async def delete_pattern(self, pattern: Pattern) -> None:
        """Delete a pattern."""
        await self.db.delete(pattern)
        await self.db.flush()
    
    async def link_pattern_to_entry(
        self,
        pattern: Pattern,
        entry: Entry,
        was_successful: bool = True,
    ) -> None:
        """Link a pattern to an entry."""
        # Check if already linked
        stmt = select(entry_patterns).where(
            and_(
                entry_patterns.c.entry_id == entry.id,
                entry_patterns.c.pattern_id == pattern.id,
            )
        )
        existing = await self.db.execute(stmt)
        
        if not existing.first():
            # Insert link
            await self.db.execute(
                entry_patterns.insert().values(
                    entry_id=entry.id,
                    pattern_id=pattern.id,
                )
            )
            
            # Update usage count
            pattern.usage_count += 1
            if was_successful:
                pattern.success_count += 1
            
            await self.db.flush()
    
    async def add_template(
        self,
        pattern: Pattern,
        data: PatternTemplateCreate,
    ) -> PatternTemplate:
        """Add a code template to a pattern."""
        template = PatternTemplate(
            pattern_id=pattern.id,
            language=data.language,
            template_code=data.template_code,
            when_to_use=data.when_to_use,
            example_problem=data.example_problem,
            time_complexity=data.time_complexity,
            space_complexity=data.space_complexity,
            key_insight=data.key_insight,
            common_mistakes=data.common_mistakes,
            difficulty_rating=data.difficulty_rating,
        )
        
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        
        return template
    
    async def get_most_used_patterns(
        self,
        user_id: int,
        limit: int = 5,
    ) -> list[Pattern]:
        """Get most frequently used patterns."""
        result = await self.db.execute(
            select(Pattern)
            .where(Pattern.user_id == user_id)
            .order_by(Pattern.usage_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_cross_domain_patterns(self, user_id: int) -> list[Pattern]:
        """Get patterns used across multiple domains."""
        result = await self.db.execute(
            select(Pattern)
            .options(selectinload(Pattern.entries))
            .where(Pattern.user_id == user_id)
        )
        patterns = result.scalars().all()
        
        # Filter to only cross-domain patterns
        return [p for p in patterns if p.is_cross_domain]
    
    async def search_patterns(
        self,
        user_id: int,
        query: str,
    ) -> list[Pattern]:
        """Search patterns by name or description."""
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Pattern)
            .where(
                and_(
                    Pattern.user_id == user_id,
                    func.lower(Pattern.name).like(search_term.lower())
                )
            )
            .order_by(Pattern.usage_count.desc())
            .limit(10)
        )
        return list(result.scalars().all())
