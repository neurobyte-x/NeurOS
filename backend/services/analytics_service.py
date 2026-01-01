"""
Analytics service - tracking and insights.

WHY: Data-driven improvement requires tracking.
This service provides:
- Daily statistics
- Progress tracking
- Insight generation
- Revision management
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from models import (
    Entry, Pattern, Reflection, EntryPattern,
    BlockerAnalytics, RevisionHistory, DailyStats
)
from models.entry import EntryType


class AnalyticsService:
    """
    Service for analytics and insights.
    
    WHY: Track learning patterns over time to:
    - Identify strengths and weaknesses
    - Measure improvement
    - Guide revision schedule
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_revision(
        self,
        entry_id: Optional[int] = None,
        pattern_id: Optional[int] = None,
        revision_type: str = "entry",
        recall_quality: int = 3,
        confidence_after: Optional[int] = None,
        revision_notes: Optional[str] = None,
        time_spent_minutes: Optional[int] = None,
    ) -> RevisionHistory:
        """
        Record a revision session.
        
        WHY: Track when and how well you reviewed something.
        Supports spaced repetition scheduling.
        """
        revision = RevisionHistory(
            entry_id=entry_id,
            pattern_id=pattern_id,
            revision_type=revision_type,
            recall_quality=recall_quality,
            confidence_after=confidence_after,
            revision_notes=revision_notes,
            time_spent_minutes=time_spent_minutes,
            revised_at=datetime.utcnow(),
            next_review_at=self._calculate_next_review(recall_quality),
        )
        
        self.db.add(revision)
        
        if entry_id and confidence_after:
            entry = self.db.query(Entry).filter(Entry.id == entry_id).first()
            if entry and entry.reflection:
                entry.reflection.confidence_level = confidence_after
        
        self.db.commit()
        self.db.refresh(revision)
        
        return revision
    
    def _calculate_next_review(self, recall_quality: int) -> datetime:
        """
        Calculate next review date based on recall quality.
        
        WHY: Simple spaced repetition - good recall = longer interval.
        
        Quality 1: Review tomorrow
        Quality 2: Review in 2 days
        Quality 3: Review in 4 days
        Quality 4: Review in 7 days
        Quality 5: Review in 14 days
        """
        intervals = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}
        days = intervals.get(recall_quality, 4)
        return datetime.utcnow() + timedelta(days=days)
    
    def get_daily_stats(
        self, 
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Get statistics for a specific day.
        
        WHY: Dashboard view of daily activity.
        """
        if date is None:
            date = datetime.utcnow()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        entries_by_type = {}
        for entry_type in EntryType:
            count = self.db.query(func.count(Entry.id)).filter(
                Entry.created_at >= start_of_day,
                Entry.created_at < end_of_day,
                Entry.entry_type == entry_type,
            ).scalar()
            entries_by_type[entry_type.value] = count
        
        total_entries = sum(entries_by_type.values())
        
        patterns_used = self.db.query(func.count(func.distinct(EntryPattern.pattern_id))).filter(
            EntryPattern.created_at >= start_of_day,
            EntryPattern.created_at < end_of_day,
        ).scalar()
        
        new_patterns = self.db.query(func.count(Pattern.id)).filter(
            Pattern.created_at >= start_of_day,
            Pattern.created_at < end_of_day,
        ).scalar()
        
        total_time = self.db.query(func.sum(Entry.time_spent_minutes)).filter(
            Entry.created_at >= start_of_day,
            Entry.created_at < end_of_day,
            Entry.time_spent_minutes.isnot(None),
        ).scalar() or 0
        
        avg_insight_time = self.db.query(func.avg(Reflection.time_to_insight_minutes)).join(Entry).filter(
            Entry.created_at >= start_of_day,
            Entry.created_at < end_of_day,
            Reflection.time_to_insight_minutes.isnot(None),
        ).scalar()
        
        return {
            "date": start_of_day.isoformat(),
            "entries_total": total_entries,
            "entries_by_type": entries_by_type,
            "patterns_used": patterns_used,
            "new_patterns": new_patterns,
            "total_time_minutes": total_time,
            "avg_time_to_insight": round(avg_insight_time, 1) if avg_insight_time else None,
        }
    
    def get_weekly_summary(self, weeks_back: int = 1) -> Dict:
        """
        Get summary for the past week.
        
        WHY: Weekly review helps identify trends.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        daily_stats = []
        current = start_date
        while current < end_date:
            stats = self.get_daily_stats(current)
            daily_stats.append(stats)
            current += timedelta(days=1)
        
        total_entries = sum(d["entries_total"] for d in daily_stats)
        total_time = sum(d["total_time_minutes"] for d in daily_stats)
        
        domain_totals = {}
        for stats in daily_stats:
            for domain, count in stats["entries_by_type"].items():
                domain_totals[domain] = domain_totals.get(domain, 0) + count
        
        most_active_domain = max(domain_totals.items(), key=lambda x: x[1])[0] if domain_totals else None
        
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_entries": total_entries,
            "total_time_minutes": total_time,
            "most_active_domain": most_active_domain,
            "daily_breakdown": daily_stats,
            "domains_breakdown": domain_totals,
        }
    
    def get_progress_insights(self) -> List[Dict]:
        """
        Generate insights about learning progress.
        
        WHY: High-level insights help guide focus.
        """
        insights = []
        
        streak = self._calculate_streak()
        if streak > 0:
            insights.append({
                "type": "progress",
                "title": f"🔥 {streak}-day streak!",
                "description": f"You've logged learning entries for {streak} consecutive days.",
                "priority": 1,
            })
        
        domain_counts = {}
        for entry_type in EntryType:
            count = self.db.query(func.count(Entry.id)).filter(
                Entry.entry_type == entry_type,
                Entry.is_complete == True,
            ).scalar()
            domain_counts[entry_type.value] = count
        
        total = sum(domain_counts.values())
        if total > 0:
            dominant = max(domain_counts.items(), key=lambda x: x[1])
            weakest = min(domain_counts.items(), key=lambda x: x[1])
            
            if dominant[1] > 0.6 * total:
                insights.append({
                    "type": "suggestion",
                    "title": f"📊 Focus imbalance",
                    "description": f"{dominant[0]} dominates ({dominant[1]}/{total}). Consider diversifying to {weakest[0]}.",
                    "priority": 2,
                })
        
        high_success_patterns = self.db.query(Pattern).filter(
            Pattern.usage_count >= 5,
            Pattern.success_rate >= 0.8,
        ).all()
        
        if high_success_patterns:
            pattern_names = ", ".join(p.name for p in high_success_patterns[:3])
            insights.append({
                "type": "strength",
                "title": "💪 Mastered patterns",
                "description": f"High success rate with: {pattern_names}",
                "priority": 2,
            })
        
        low_success_patterns = self.db.query(Pattern).filter(
            Pattern.usage_count >= 3,
            Pattern.success_rate < 0.5,
        ).order_by(Pattern.success_rate).limit(3).all()
        
        if low_success_patterns:
            pattern_names = ", ".join(p.name for p in low_success_patterns)
            insights.append({
                "type": "weakness",
                "title": "📈 Improvement areas",
                "description": f"Lower success with: {pattern_names}. Consider focused practice.",
                "priority": 1,
            })
        
        total_entries = self.db.query(func.count(Entry.id)).scalar()
        complete_entries = self.db.query(func.count(Entry.id)).filter(
            Entry.is_complete == True
        ).scalar()
        
        if total_entries > 0:
            completion_rate = complete_entries / total_entries
            if completion_rate < 0.8:
                incomplete = total_entries - complete_entries
                insights.append({
                    "type": "suggestion",
                    "title": "📝 Incomplete entries",
                    "description": f"{incomplete} entries await reflection. Complete them to solidify learning.",
                    "priority": 1,
                })
        
        return sorted(insights, key=lambda x: x["priority"])
    
    def _calculate_streak(self) -> int:
        """Calculate consecutive days with completed entries."""
        streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            start = datetime.combine(current_date, datetime.min.time())
            end = start + timedelta(days=1)
            
            has_entry = self.db.query(Entry).filter(
                Entry.created_at >= start,
                Entry.created_at < end,
                Entry.is_complete == True,
            ).first()
            
            if has_entry:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_blocker_analysis(self) -> Dict:
        """
        Analyze blocker patterns.
        
        WHY: Understanding systematic blockers enables
        targeted improvement.
        """
        blockers = self.db.query(BlockerAnalytics).order_by(
            desc(BlockerAnalytics.occurrence_count)
        ).all()
        
        flagged = [b for b in blockers if b.is_flagged]
        
        return {
            "total_unique_blockers": len(blockers),
            "flagged_blockers": len(flagged),
            "top_blockers": [
                {
                    "text": b.blocker_text[:100],
                    "count": b.occurrence_count,
                    "is_flagged": b.is_flagged,
                    "first_seen": b.first_seen_at.isoformat(),
                    "last_seen": b.last_seen_at.isoformat(),
                }
                for b in blockers[:10]
            ],
        }
    
    def get_revision_queue(self) -> List[Dict]:
        """
        Get items due for revision.
        
        WHY: Spaced repetition queue for daily review.
        """
        now = datetime.utcnow()
        
        due_items = self.db.query(RevisionHistory).filter(
            RevisionHistory.next_review_at <= now
        ).order_by(RevisionHistory.next_review_at).all()
        
        queue = []
        seen_entries = set()
        seen_patterns = set()
        
        for item in due_items:
            if item.entry_id and item.entry_id in seen_entries:
                continue
            if item.pattern_id and item.pattern_id in seen_patterns:
                continue
            
            if item.entry_id:
                seen_entries.add(item.entry_id)
                entry = self.db.query(Entry).filter(Entry.id == item.entry_id).first()
                if entry:
                    queue.append({
                        "type": "entry",
                        "id": entry.id,
                        "title": entry.title,
                        "key_pattern": entry.reflection.key_pattern if entry.reflection else None,
                        "last_recall_quality": item.recall_quality,
                        "due_since": (now - item.next_review_at).days,
                    })
            
            if item.pattern_id:
                seen_patterns.add(item.pattern_id)
                pattern = self.db.query(Pattern).filter(Pattern.id == item.pattern_id).first()
                if pattern:
                    queue.append({
                        "type": "pattern",
                        "id": pattern.id,
                        "title": pattern.name,
                        "description": pattern.description,
                        "last_recall_quality": item.recall_quality,
                        "due_since": (now - item.next_review_at).days,
                    })
        
        return queue
