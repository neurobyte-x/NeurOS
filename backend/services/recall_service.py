"""
Recall service - the intelligence layer of Thinking OS.

WHY: This is what makes Thinking OS more than a notes app.
The recall service:
- Surfaces similar past entries before new work
- Identifies repeated blockers (systematic weaknesses)
- Suggests what to revise based on history
- Provides "you struggled with X" warnings

PHILOSOPHY: Your past struggles are your best teacher.
This service makes that wisdom accessible.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import json

from models import Entry, Pattern, Reflection, EntryPattern, BlockerAnalytics, RevisionHistory
from models.entry import EntryType
from config import settings


class RecallService:
    """
    Intelligence layer for surfacing relevant past experiences.
    
    WHY: Before starting new work, you should know:
    - What similar problems you've solved
    - What patterns might apply
    - What blockers to watch out for
    - What needs revision
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_similar_entries(
        self,
        title: Optional[str] = None,
        entry_type: Optional[EntryType] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find entries similar to the given context.
        
        WHY: Before solving a problem, see if you've solved
        something similar. Learn from your past self.
        
        Current implementation: Keyword matching
        Future: Embedding-based semantic search
        """
        results = []
        
        # Build search terms
        search_terms = set()
        if title:
            search_terms.update(title.lower().split())
        if description:
            search_terms.update(description.lower().split())
        if keywords:
            search_terms.update(k.lower() for k in keywords)
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        search_terms -= stop_words
        
        if not search_terms:
            # Return recent entries of same type if no search terms
            query = self.db.query(Entry).filter(Entry.is_complete == True)
            if entry_type:
                query = query.filter(Entry.entry_type == entry_type)
            entries = query.order_by(desc(Entry.created_at)).limit(limit).all()
            
            for entry in entries:
                results.append(self._entry_to_similar_result(entry, 0.5, "Recent entry"))
            return results
        
        # Search entries
        query = self.db.query(Entry).filter(Entry.is_complete == True)
        if entry_type:
            query = query.filter(Entry.entry_type == entry_type)
        
        entries = query.all()
        
        # Score each entry
        scored_entries = []
        for entry in entries:
            score, reason = self._calculate_similarity(entry, search_terms)
            if score > 0:
                scored_entries.append((entry, score, reason))
        
        # Sort by score
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches
        for entry, score, reason in scored_entries[:limit]:
            results.append(self._entry_to_similar_result(entry, score, reason))
        
        return results
    
    def _calculate_similarity(
        self, 
        entry: Entry, 
        search_terms: set
    ) -> tuple:
        """
        Calculate similarity score between entry and search terms.
        
        WHY: Simple keyword matching now, but architecture
        supports embedding-based search later.
        """
        score = 0.0
        reasons = []
        
        # Title matching
        title_words = set(entry.title.lower().split())
        title_overlap = len(search_terms & title_words)
        if title_overlap > 0:
            score += title_overlap * 0.3
            reasons.append("Title match")
        
        # Reflection matching
        if entry.reflection:
            reflection_text = " ".join([
                entry.reflection.context or "",
                entry.reflection.key_pattern or "",
                entry.reflection.initial_blocker or "",
            ]).lower()
            reflection_words = set(reflection_text.split())
            reflection_overlap = len(search_terms & reflection_words)
            if reflection_overlap > 0:
                score += reflection_overlap * 0.2
                reasons.append("Reflection match")
        
        # Pattern matching (check associated patterns)
        for ep in entry.patterns:
            pattern_words = set(ep.pattern.name.lower().split())
            if search_terms & pattern_words:
                score += 0.2
                reasons.append(f"Pattern: {ep.pattern.name}")
                break
        
        return score, ", ".join(reasons) if reasons else "General match"
    
    def _entry_to_similar_result(
        self, 
        entry: Entry, 
        score: float, 
        reason: str
    ) -> Dict:
        """Convert entry to similar result dict."""
        days_ago = (datetime.utcnow() - entry.created_at).days
        
        return {
            "entry_id": entry.id,
            "entry_title": entry.title,
            "entry_type": entry.entry_type.value,
            "similarity_score": min(score, 1.0),
            "similarity_reason": reason,
            "key_pattern": entry.reflection.key_pattern if entry.reflection else None,
            "days_ago": days_ago,
        }
    
    def get_blocker_warnings(
        self, 
        context: Optional[str] = None,
        entry_type: Optional[EntryType] = None
    ) -> List[str]:
        """
        Get warnings about repeated blockers.
        
        WHY: "You've struggled with X three times" is powerful
        feedback that helps focus improvement efforts.
        """
        warnings = []
        
        # Get flagged blockers
        flagged = self.db.query(BlockerAnalytics).filter(
            BlockerAnalytics.is_flagged == True
        ).all()
        
        for blocker in flagged:
            warnings.append(
                f"⚠️ Repeated blocker ({blocker.occurrence_count}x): "
                f"{blocker.blocker_text[:100]}..."
            )
        
        # Check recent blockers in same domain
        if entry_type:
            recent_entries = self.db.query(Entry).filter(
                Entry.entry_type == entry_type,
                Entry.is_complete == True,
                Entry.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Group blockers by similarity (simple approach)
            blocker_counts = {}
            for entry in recent_entries:
                if entry.reflection:
                    blocker = entry.reflection.initial_blocker[:50]
                    blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
            
            for blocker, count in blocker_counts.items():
                if count >= settings.BLOCKER_REPEAT_THRESHOLD:
                    warnings.append(
                        f"🔄 In last 30 days, similar blocker appeared {count}x: {blocker}..."
                    )
        
        return warnings
    
    def get_relevant_patterns(
        self,
        title: Optional[str] = None,
        entry_type: Optional[EntryType] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Suggest patterns that might be relevant.
        
        WHY: Before solving, consider which patterns apply.
        This is the "what have I learned?" moment.
        """
        results = []
        
        # Build search terms
        search_terms = set()
        if title:
            search_terms.update(title.lower().split())
        if keywords:
            search_terms.update(k.lower() for k in keywords)
        
        # Get patterns for this domain
        query = self.db.query(Pattern)
        if entry_type:
            query = query.filter(
                Pattern.domain_tags.ilike(f"%{entry_type.value}%")
            )
        
        patterns = query.all()
        
        # Score patterns
        scored = []
        for pattern in patterns:
            score = 0
            reason = []
            
            # Name match
            pattern_words = set(pattern.name.lower().split())
            if search_terms & pattern_words:
                score += 0.4
                reason.append("Name match")
            
            # Trigger match
            if pattern.common_triggers:
                trigger_words = set(pattern.common_triggers.lower().split())
                if search_terms & trigger_words:
                    score += 0.3
                    reason.append("Trigger match")
            
            # Usage bonus
            score += min(pattern.usage_count / 20, 0.2)
            
            # Success rate bonus
            score += pattern.success_rate * 0.1
            
            if score > 0:
                scored.append((pattern, score, ", ".join(reason) or "Domain match"))
        
        # Sort and return
        scored.sort(key=lambda x: x[1], reverse=True)
        
        for pattern, score, reason in scored[:limit]:
            results.append({
                "pattern_id": pattern.id,
                "pattern_name": pattern.name,
                "description": pattern.description,
                "relevance_score": min(score, 1.0),
                "match_reason": reason,
                "usage_count": pattern.usage_count,
                "success_rate": pattern.success_rate,
                "common_triggers": pattern.common_triggers,
                "common_mistakes": pattern.common_mistakes,
            })
        
        return results
    
    def get_revision_suggestions(self, limit: int = 5) -> List[Dict]:
        """
        Suggest items that need revision.
        
        WHY: Spaced repetition works. This identifies what
        needs reinforcement based on time and confidence.
        
        Criteria:
        - Low confidence entries
        - Not reviewed recently
        - Patterns with low success rate
        """
        suggestions = []
        
        # Low confidence entries
        low_confidence = self.db.query(Entry).join(Reflection).filter(
            Reflection.confidence_level <= 2,
            Entry.is_complete == True
        ).order_by(Entry.created_at).limit(3).all()
        
        for entry in low_confidence:
            suggestions.append({
                "type": "revision_due",
                "title": f"Review: {entry.title}",
                "description": f"Low confidence ({entry.reflection.confidence_level}/5) on pattern: {entry.reflection.key_pattern}",
                "priority": 1,
                "related_entry_id": entry.id,
                "action_text": "Revisit and re-attempt",
            })
        
        # Old entries not recently reviewed
        cutoff_date = datetime.utcnow() - timedelta(days=settings.REVISION_WINDOW_DAYS)
        old_entries = self.db.query(Entry).filter(
            Entry.is_complete == True,
            Entry.created_at < cutoff_date,
        ).order_by(Entry.created_at).limit(3).all()
        
        # Check if they've been revised
        for entry in old_entries:
            recent_revision = self.db.query(RevisionHistory).filter(
                RevisionHistory.entry_id == entry.id,
                RevisionHistory.revised_at >= cutoff_date
            ).first()
            
            if not recent_revision:
                days_old = (datetime.utcnow() - entry.created_at).days
                suggestions.append({
                    "type": "revision_due",
                    "title": f"Review: {entry.title}",
                    "description": f"Not reviewed in {days_old} days",
                    "priority": 2,
                    "related_entry_id": entry.id,
                    "action_text": "Test your recall",
                })
        
        # Patterns with low success rate
        low_success_patterns = self.db.query(Pattern).filter(
            Pattern.usage_count >= 2,
            Pattern.success_rate < 0.5
        ).order_by(Pattern.success_rate).limit(3).all()
        
        for pattern in low_success_patterns:
            suggestions.append({
                "type": "pattern_weakness",
                "title": f"Pattern weakness: {pattern.name}",
                "description": f"Success rate: {pattern.success_rate:.0%} across {pattern.usage_count} uses",
                "priority": 2,
                "related_pattern_id": pattern.id,
                "action_text": "Practice this pattern",
            })
        
        # Sort by priority and limit
        suggestions.sort(key=lambda x: x["priority"])
        return suggestions[:limit]
    
    def get_full_recall_context(
        self,
        title: Optional[str] = None,
        entry_type: Optional[EntryType] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get complete recall context before starting new work.
        
        WHY: One-stop method to get all relevant history
        before diving into a new problem/task.
        """
        return {
            "similar_entries": self.get_similar_entries(
                title, entry_type, description, keywords
            ),
            "relevant_patterns": self.get_relevant_patterns(
                title, entry_type, keywords
            ),
            "blocker_warnings": self.get_blocker_warnings(description, entry_type),
            "revision_suggestions": self.get_revision_suggestions(),
        }
    
    def record_blocker(self, entry_id: int, blocker_text: str):
        """
        Record a blocker for analytics.
        
        WHY: Track blockers to identify systematic weaknesses.
        Called when a reflection is saved.
        """
        # Normalize blocker text
        normalized = blocker_text.strip().lower()[:200]
        
        # Look for similar existing blocker
        existing = self.db.query(BlockerAnalytics).filter(
            BlockerAnalytics.blocker_text.ilike(f"%{normalized[:50]}%")
        ).first()
        
        if existing:
            # Update existing
            existing.occurrence_count += 1
            existing.last_seen_at = datetime.utcnow()
            
            # Parse and update entry IDs
            entry_ids = json.loads(existing.entry_ids)
            if entry_id not in entry_ids:
                entry_ids.append(entry_id)
                existing.entry_ids = json.dumps(entry_ids)
            
            # Flag if threshold exceeded
            if existing.occurrence_count >= settings.BLOCKER_REPEAT_THRESHOLD:
                existing.is_flagged = True
        else:
            # Create new blocker record
            blocker = BlockerAnalytics(
                blocker_text=normalized,
                entry_ids=json.dumps([entry_id]),
                occurrence_count=1,
            )
            self.db.add(blocker)
        
        self.db.commit()
