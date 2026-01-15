"""
NeurOS 2.0 Knowledge Node Model

Nodes in the personal knowledge graph.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer, 
    String, Text, Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.knowledge_edge import KnowledgeEdge


class NodeType(str, enum.Enum):
    """Types of knowledge nodes."""
    CONCEPT = "concept"        # Abstract concept (e.g., "Dynamic Programming")
    TECHNIQUE = "technique"    # Specific technique (e.g., "Memoization")
    PATTERN = "pattern"        # Thinking pattern (linked to Pattern model)
    ALGORITHM = "algorithm"    # Specific algorithm (e.g., "Dijkstra's")
    DATA_STRUCTURE = "data_structure"  # Data structure (e.g., "Segment Tree")
    TOOL = "tool"              # Tool or technology (e.g., "Redis")
    DOMAIN = "domain"          # High-level domain (e.g., "Backend", "ML")


class MasteryLevel(int, enum.Enum):
    """Mastery levels for knowledge nodes."""
    NOVICE = 1        # Just learned, needs practice
    BEGINNER = 2      # Can apply with reference
    INTERMEDIATE = 3  # Can apply independently
    ADVANCED = 4      # Can apply efficiently
    EXPERT = 5        # Can teach others


class KnowledgeNode(Base):
    """
    Node in the personal knowledge graph.
    
    PURPOSE:
    Represent concepts, techniques, and patterns as nodes
    that can be connected to show relationships and dependencies.
    
    VISUAL MAPPING:
    - Node color: Based on decay_score (green -> yellow -> red)
    - Node size: Based on mastery_level (1-5)
    - Connections: Show prerequisites, related concepts
    """
    __tablename__ = "knowledge_nodes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Core identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Categorization
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType),
        default=NodeType.CONCEPT,
    )
    domain: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Primary domain (DSA, Backend, etc.)",
    )
    
    # Learning state
    mastery_level: Mapped[int] = mapped_column(
        Integer,
        default=MasteryLevel.NOVICE,
    )
    decay_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
        comment="Current retention score (0-100)",
    )
    
    # Practice tracking
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    times_practiced: Mapped[int] = mapped_column(Integer, default=0)
    
    # External references
    linked_pattern_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="If this node represents a Pattern",
    )
    linked_entry_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Origin entry if auto-generated",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="knowledge_nodes")
    
    outgoing_edges: Mapped[list["KnowledgeEdge"]] = relationship(
        "KnowledgeEdge",
        foreign_keys="KnowledgeEdge.from_node_id",
        back_populates="from_node",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["KnowledgeEdge"]] = relationship(
        "KnowledgeEdge",
        foreign_keys="KnowledgeEdge.to_node_id",
        back_populates="to_node",
        cascade="all, delete-orphan",
    )
    
    @property
    def color_indicator(self) -> str:
        """Get color based on decay score for visualization."""
        if self.decay_score >= 70:
            return "green"
        elif self.decay_score >= 40:
            return "yellow"
        else:
            return "red"
    
    @property
    def size_factor(self) -> float:
        """Get size factor based on mastery for visualization."""
        return 0.5 + (self.mastery_level * 0.3)  # 0.8 to 2.0
    
    @property
    def prerequisites(self) -> list["KnowledgeNode"]:
        """Get prerequisite nodes."""
        return [
            edge.from_node for edge in self.incoming_edges
            if edge.relationship_type == "prerequisite"
        ]
    
    @property
    def related_nodes(self) -> list["KnowledgeNode"]:
        """Get related nodes (outgoing)."""
        return [
            edge.to_node for edge in self.outgoing_edges
            if edge.relationship_type == "related"
        ]
    
    def __repr__(self) -> str:
        return (
            f"<KnowledgeNode(id={self.id}, name='{self.name}', "
            f"type={self.node_type}, mastery={self.mastery_level})>"
        )
