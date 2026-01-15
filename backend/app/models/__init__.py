"""
NeurOS 2.0 Models Package

All SQLAlchemy models for the application.
"""

from app.models.user import User
from app.models.entry import Entry, EntryType, DifficultyLevel
from app.models.reflection import Reflection
from app.models.pattern import Pattern, entry_patterns
from app.models.srs_review import SRSReview, ReviewItemType, ReviewStatus
from app.models.decay_tracking import DecayTracking, TrackableType
from app.models.knowledge_node import KnowledgeNode, NodeType, MasteryLevel
from app.models.knowledge_edge import KnowledgeEdge, RelationshipType
from app.models.pattern_template import PatternTemplate, ProgrammingLanguage


__all__ = [
    # Models
    "User",
    "Entry",
    "Reflection",
    "Pattern",
    "SRSReview",
    "DecayTracking",
    "KnowledgeNode",
    "KnowledgeEdge",
    "PatternTemplate",
    # Association tables
    "entry_patterns",
    # Enums
    "EntryType",
    "DifficultyLevel",
    "ReviewItemType",
    "ReviewStatus",
    "TrackableType",
    "NodeType",
    "MasteryLevel",
    "RelationshipType",
    "ProgrammingLanguage",
]
