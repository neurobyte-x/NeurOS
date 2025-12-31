"""
Services package initialization.

WHY: Business logic is separated from routes for:
- Testability (services can be unit tested)
- Reusability (multiple routes can use same service)
- Clean separation of concerns
"""

from services.entry_service import EntryService
from services.pattern_service import PatternService
from services.recall_service import RecallService
from services.analytics_service import AnalyticsService
from services.ai_service import AIService, get_ai_service

__all__ = [
    "EntryService",
    "PatternService", 
    "RecallService",
    "AnalyticsService",
    "AIService",
    "get_ai_service",
]
