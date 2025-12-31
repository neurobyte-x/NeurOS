"""
Schemas package initialization.

WHY: Clean schema imports for routes and services.
Schemas handle validation and serialization.
"""

from schemas.entry import (
    EntryCreate, EntryUpdate, EntryResponse, 
    EntryWithReflection, EntryListResponse
)
from schemas.reflection import (
    ReflectionCreate, ReflectionUpdate, ReflectionResponse
)
from schemas.pattern import (
    PatternCreate, PatternUpdate, PatternResponse,
    PatternWithEntries, EntryPatternCreate
)
from schemas.analytics import (
    BlockerAnalyticsResponse, RevisionCreate,
    RevisionResponse, DailyStatsResponse,
    RecallSuggestion, InsightResponse
)

__all__ = [
    # Entry schemas
    "EntryCreate",
    "EntryUpdate", 
    "EntryResponse",
    "EntryWithReflection",
    "EntryListResponse",
    
    # Reflection schemas
    "ReflectionCreate",
    "ReflectionUpdate",
    "ReflectionResponse",
    
    # Pattern schemas
    "PatternCreate",
    "PatternUpdate",
    "PatternResponse",
    "PatternWithEntries",
    "EntryPatternCreate",
    
    # Analytics schemas
    "BlockerAnalyticsResponse",
    "RevisionCreate",
    "RevisionResponse",
    "DailyStatsResponse",
    "RecallSuggestion",
    "InsightResponse",
]
