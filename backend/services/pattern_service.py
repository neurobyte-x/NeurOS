"""
Pattern service - manage user-defined thinking patterns.

WHY: Patterns are the transferable knowledge units.
This service manages pattern lifecycle, discovery,
and association with entries.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from models import Pattern, EntryPattern, Entry
from schemas.pattern import PatternCreate, PatternUpdate


class PatternService:
    """
    Service for managing thinking patterns.
    
    WHY: Centralizes pattern logic including:
    - CRUD operations
    - Pattern discovery and suggestions
    - Usage tracking
    - Cross-domain pattern analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_pattern(self, pattern_data: PatternCreate) -> Pattern:
        """
        Create a new user-defined pattern.
        
        WHY: Patterns are user-defined, not textbook.
        This preserves personal vocabulary.
        """
        existing = self.db.query(Pattern).filter(
            func.lower(Pattern.name) == pattern_data.name.lower()
        ).first()
        
        if existing:
            raise ValueError(f"Pattern '{pattern_data.name}' already exists")
        
        pattern = Pattern(
            name=pattern_data.name,
            description=pattern_data.description,
            domain_tags=pattern_data.domain_tags,
            common_triggers=pattern_data.common_triggers,
            common_mistakes=pattern_data.common_mistakes,
            usage_count=0,
            success_rate=0.0,
        )
        
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        
        return pattern
    
    def get_pattern(self, pattern_id: int) -> Optional[Pattern]:
        """Get pattern by ID."""
        return self.db.query(Pattern).filter(Pattern.id == pattern_id).first()
    
    def get_pattern_by_name(self, name: str) -> Optional[Pattern]:
        """Get pattern by name (case-insensitive)."""
        return self.db.query(Pattern).filter(
            func.lower(Pattern.name) == name.lower()
        ).first()
    
    def get_patterns(
        self,
        page: int = 1,
        page_size: int = 50,
        domain_tag: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "usage_count",  # usage_count, name, created_at
    ) -> Tuple[List[Pattern], int]:
        """
        Get paginated list of patterns.
        
        WHY: Supports pattern browsing and discovery.
        """
        query = self.db.query(Pattern)
        
        if domain_tag:
            query = query.filter(Pattern.domain_tags.ilike(f"%{domain_tag}%"))
        
        if search_query:
            query = query.filter(
                (Pattern.name.ilike(f"%{search_query}%")) |
                (Pattern.description.ilike(f"%{search_query}%"))
            )
        
        total = query.count()
        
        if sort_by == "usage_count":
            query = query.order_by(desc(Pattern.usage_count))
        elif sort_by == "name":
            query = query.order_by(Pattern.name)
        else:
            query = query.order_by(desc(Pattern.created_at))
        
        patterns = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return patterns, total
    
    def update_pattern(
        self, 
        pattern_id: int, 
        pattern_data: PatternUpdate
    ) -> Optional[Pattern]:
        """Update an existing pattern."""
        pattern = self.db.query(Pattern).filter(Pattern.id == pattern_id).first()
        
        if not pattern:
            return None
        
        update_data = pattern_data.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            existing = self.db.query(Pattern).filter(
                func.lower(Pattern.name) == update_data["name"].lower(),
                Pattern.id != pattern_id
            ).first()
            if existing:
                raise ValueError(f"Pattern '{update_data['name']}' already exists")
        
        for field, value in update_data.items():
            setattr(pattern, field, value)
        
        pattern.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pattern)
        
        return pattern
    
    def delete_pattern(self, pattern_id: int) -> bool:
        """Delete a pattern."""
        pattern = self.db.query(Pattern).filter(Pattern.id == pattern_id).first()
        
        if not pattern:
            return False
        
        self.db.delete(pattern)
        self.db.commit()
        
        return True
    
    def associate_pattern_with_entry(
        self,
        entry_id: int,
        pattern_id: int,
        relevance_score: float = 1.0,
        application_notes: Optional[str] = None,
        was_successful: int = 1,
    ) -> EntryPattern:
        """
        Associate a pattern with an entry.
        
        WHY: One entry can demonstrate multiple patterns.
        This builds the knowledge graph.
        """
        existing = self.db.query(EntryPattern).filter(
            EntryPattern.entry_id == entry_id,
            EntryPattern.pattern_id == pattern_id
        ).first()
        
        if existing:
            existing.relevance_score = relevance_score
            existing.application_notes = application_notes
            existing.was_successful = was_successful
            self.db.commit()
            return existing
        
        entry_pattern = EntryPattern(
            entry_id=entry_id,
            pattern_id=pattern_id,
            relevance_score=relevance_score,
            application_notes=application_notes,
            was_successful=was_successful,
        )
        
        self.db.add(entry_pattern)
        
        pattern = self.db.query(Pattern).filter(Pattern.id == pattern_id).first()
        if pattern:
            pattern.usage_count += 1
            pattern.last_used_at = datetime.utcnow()
            self._update_success_rate(pattern)
        
        self.db.commit()
        self.db.refresh(entry_pattern)
        
        return entry_pattern
    
    def _update_success_rate(self, pattern: Pattern):
        """
        Recalculate pattern success rate.
        
        WHY: Track how often applying this pattern leads to success.
        """
        associations = self.db.query(EntryPattern).filter(
            EntryPattern.pattern_id == pattern.id
        ).all()
        
        if not associations:
            pattern.success_rate = 0.0
            return
        
        successful = sum(1 for a in associations if a.was_successful == 1)
        pattern.success_rate = successful / len(associations)
    
    def get_pattern_with_entries(self, pattern_id: int) -> Optional[Pattern]:
        """Get pattern with all associated entries."""
        return self.db.query(Pattern).options(
            joinedload(Pattern.entries).joinedload(EntryPattern.entry)
        ).filter(Pattern.id == pattern_id).first()
    
    def get_or_create_pattern(self, name: str) -> Pattern:
        """
        Get existing pattern or create new one.
        
        WHY: Convenience method for inline pattern creation
        during entry saving.
        """
        pattern = self.get_pattern_by_name(name)
        
        if pattern:
            return pattern
        
        return self.create_pattern(PatternCreate(name=name))
    
    def suggest_patterns_for_entry(self, entry: Entry) -> List[Pattern]:
        """
        Suggest relevant patterns for an entry.
        
        WHY: Help user discover patterns they might not remember.
        Uses keyword matching now, embeddings later.
        
        Args:
            entry: The entry to suggest patterns for
            
        Returns:
            List of potentially relevant patterns
        """
        domain_patterns = self.db.query(Pattern).filter(
            Pattern.domain_tags.ilike(f"%{entry.entry_type.value}%")
        ).all()
        
        frequent_patterns = self.db.query(Pattern).order_by(
            desc(Pattern.usage_count)
        ).limit(10).all()
        
        all_patterns = {p.id: p for p in domain_patterns + frequent_patterns}
        
        title_words = set(entry.title.lower().split())
        scored_patterns = []
        
        for pattern in all_patterns.values():
            score = 0
            pattern_words = set(pattern.name.lower().split())
            
            overlap = len(title_words & pattern_words)
            if overlap > 0:
                score += overlap * 2
            
            if pattern.domain_tags and entry.entry_type.value in pattern.domain_tags:
                score += 1
            
            score += min(pattern.usage_count / 10, 1)
            
            if score > 0:
                scored_patterns.append((pattern, score))
        
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored_patterns[:5]]
    
    def get_cross_domain_patterns(self) -> List[Pattern]:
        """
        Get patterns that appear across multiple domains.
        
        WHY: These are the most valuable transferable patterns.
        """
        patterns = self.db.query(Pattern).filter(
            Pattern.domain_tags.isnot(None)
        ).all()
        
        cross_domain = []
        for pattern in patterns:
            if pattern.domain_tags:
                domains = [d.strip() for d in pattern.domain_tags.split(",")]
                if len(domains) > 1:
                    cross_domain.append(pattern)
        
        return sorted(cross_domain, key=lambda p: p.usage_count, reverse=True)
    
    def get_pattern_stats(self) -> dict:
        """Get aggregate statistics about patterns."""
        total = self.db.query(func.count(Pattern.id)).scalar()
        
        most_used = self.db.query(Pattern).order_by(
            desc(Pattern.usage_count)
        ).limit(5).all()
        
        high_success = self.db.query(Pattern).filter(
            Pattern.usage_count >= 3
        ).order_by(desc(Pattern.success_rate)).limit(5).all()
        
        unused = self.db.query(func.count(Pattern.id)).filter(
            Pattern.usage_count == 0
        ).scalar()
        
        return {
            "total_patterns": total,
            "unused_patterns": unused,
            "most_used": [{"id": p.id, "name": p.name, "count": p.usage_count} 
                          for p in most_used],
            "highest_success": [{"id": p.id, "name": p.name, "rate": p.success_rate}
                                for p in high_success],
        }
