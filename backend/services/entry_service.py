"""
Entry service - core business logic for entries.

WHY: This service enforces the core invariant:
"No entry is complete without reflection."

All entry operations go through here to ensure
data integrity and business rules.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from models import Entry, EntryType, Reflection, EntryPattern, Pattern
from schemas.entry import EntryCreate, EntryUpdate


class EntryService:
    """
    Service for managing learning entries.
    
    WHY: Centralizes entry logic including:
    - CRUD operations
    - Reflection enforcement
    - Search and filtering
    - Completion status management
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_entry(self, entry_data: EntryCreate) -> Entry:
        """
        Create a new entry (incomplete until reflection added).
        
        WHY: Entry starts incomplete. User must add reflection
        for it to be considered "done". This enforces the
        reflection-first philosophy.
        
        Args:
            entry_data: Entry creation schema
            
        Returns:
            Created entry (is_complete=False)
        """
        entry = Entry(
            title=entry_data.title,
            entry_type=entry_data.entry_type,
            source_url=entry_data.source_url,
            source_name=entry_data.source_name,
            difficulty=entry_data.difficulty,
            time_spent_minutes=entry_data.time_spent_minutes,
            code_snippet=entry_data.code_snippet,
            language=entry_data.language,
            is_complete=False,  # Always starts incomplete
            has_reflection=False,
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def get_entry(self, entry_id: int) -> Optional[Entry]:
        """Get entry by ID with all relationships loaded."""
        return self.db.query(Entry).options(
            joinedload(Entry.reflection),
            joinedload(Entry.patterns).joinedload(EntryPattern.pattern)
        ).filter(Entry.id == entry_id).first()
    
    def get_entries(
        self,
        page: int = 1,
        page_size: int = 20,
        entry_type: Optional[EntryType] = None,
        is_complete: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> Tuple[List[Entry], int]:
        """
        Get paginated list of entries with filters.
        
        WHY: Pagination and filtering support large datasets
        and focused review sessions.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            entry_type: Filter by domain
            is_complete: Filter by completion status
            search_query: Search in title
            
        Returns:
            Tuple of (entries, total_count)
        """
        query = self.db.query(Entry)
        
        if entry_type:
            query = query.filter(Entry.entry_type == entry_type)
        
        if is_complete is not None:
            query = query.filter(Entry.is_complete == is_complete)
        
        if search_query:
            query = query.filter(Entry.title.ilike(f"%{search_query}%"))
        
        total = query.count()
        
        entries = query.order_by(desc(Entry.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return entries, total
    
    def update_entry(self, entry_id: int, entry_data: EntryUpdate) -> Optional[Entry]:
        """Update an existing entry."""
        entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            return None
        
        update_data = entry_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an entry and all related data.
        
        WHY: Cascade delete handles reflection and patterns.
        """
        entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            return False
        
        self.db.delete(entry)
        self.db.commit()
        
        return True
    
    def add_reflection(self, entry_id: int, reflection: Reflection) -> Entry:
        """
        Add reflection to entry and mark as complete.
        
        WHY: This is the key operation - adding reflection
        "completes" the entry and makes it count.
        
        Args:
            entry_id: Entry to add reflection to
            reflection: The reflection object
            
        Returns:
            Updated entry with is_complete=True
        """
        entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            raise ValueError(f"Entry {entry_id} not found")
        
        if not reflection.is_complete():
            raise ValueError("Reflection is missing mandatory fields")
        
        entry.reflection = reflection
        entry.has_reflection = True
        entry.is_complete = True
        entry.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def get_entries_by_pattern(self, pattern_name: str) -> List[Entry]:
        """
        Get all entries associated with a pattern.
        
        WHY: Pattern-based retrieval for revision and analysis.
        """
        return self.db.query(Entry).join(
            EntryPattern
        ).join(
            Pattern
        ).filter(
            Pattern.name.ilike(f"%{pattern_name}%")
        ).order_by(desc(Entry.created_at)).all()
    
    def get_recent_entries_by_type(
        self, 
        entry_type: EntryType, 
        limit: int = 10
    ) -> List[Entry]:
        """Get recent entries of a specific type."""
        return self.db.query(Entry).filter(
            Entry.entry_type == entry_type,
            Entry.is_complete == True
        ).order_by(desc(Entry.created_at)).limit(limit).all()
    
    def get_incomplete_entries(self) -> List[Entry]:
        """
        Get entries without reflections.
        
        WHY: Surface entries that need completion,
        encourage reflection habit.
        """
        return self.db.query(Entry).filter(
            Entry.is_complete == False
        ).order_by(desc(Entry.created_at)).all()
    
    def search_entries(
        self,
        query: str,
        entry_types: Optional[List[EntryType]] = None,
        limit: int = 20
    ) -> List[Entry]:
        """
        Full-text search across entries.
        
        WHY: Keyword search for finding past entries.
        Future: Replace with embedding-based semantic search.
        """
        db_query = self.db.query(Entry).options(
            joinedload(Entry.reflection)
        )
        
        db_query = db_query.filter(
            (Entry.title.ilike(f"%{query}%")) |
            (Entry.reflection.has(Reflection.context.ilike(f"%{query}%"))) |
            (Entry.reflection.has(Reflection.key_pattern.ilike(f"%{query}%"))) |
            (Entry.reflection.has(Reflection.initial_blocker.ilike(f"%{query}%")))
        )
        
        if entry_types:
            db_query = db_query.filter(Entry.entry_type.in_(entry_types))
        
        return db_query.order_by(desc(Entry.created_at)).limit(limit).all()
    
    def get_entry_stats(self) -> dict:
        """
        Get aggregate statistics about entries.
        
        WHY: Dashboard overview of learning activity.
        """
        total = self.db.query(func.count(Entry.id)).scalar()
        complete = self.db.query(func.count(Entry.id)).filter(
            Entry.is_complete == True
        ).scalar()
        
        by_type = {}
        for entry_type in EntryType:
            count = self.db.query(func.count(Entry.id)).filter(
                Entry.entry_type == entry_type
            ).scalar()
            by_type[entry_type.value] = count
        
        avg_time = self.db.query(func.avg(Entry.time_spent_minutes)).filter(
            Entry.time_spent_minutes.isnot(None)
        ).scalar()
        
        return {
            "total_entries": total,
            "complete_entries": complete,
            "incomplete_entries": total - complete,
            "entries_by_type": by_type,
            "avg_time_spent_minutes": round(avg_time, 1) if avg_time else 0,
        }
