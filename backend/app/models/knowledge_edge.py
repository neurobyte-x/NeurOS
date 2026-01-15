"""
NeurOS 2.0 Knowledge Edge Model

Connections between nodes in the knowledge graph.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, 
    Integer, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.knowledge_node import KnowledgeNode


class RelationshipType(str, enum.Enum):
    """Types of relationships between knowledge nodes."""
    PREREQUISITE = "prerequisite"  # A is required before B
    RELATED = "related"            # A and B are related concepts
    CONTRAST = "contrast"          # A vs B (comparison)
    CONTAINS = "contains"          # A contains B (hierarchy)
    APPLIES_TO = "applies_to"      # Pattern A applies to problem B
    EXAMPLE_OF = "example_of"      # A is an example of B


class KnowledgeEdge(Base):
    """
    Edge (connection) between two knowledge nodes.
    
    PURPOSE:
    Represent relationships between concepts, enabling:
    - Prerequisite chains
    - Related concept discovery
    - Knowledge gap identification
    
    DIRECTION:
    from_node -> to_node
    e.g., "Binary Search" -> "Sorted Array" (prerequisite)
    meaning: Understanding sorted arrays is prerequisite for binary search
    """
    __tablename__ = "knowledge_edges"
    
    __table_args__ = (
        UniqueConstraint(
            "from_node_id", "to_node_id", "relationship_type",
            name="uq_edge_relationship"
        ),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # Connection
    from_node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationship type
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType),
        default=RelationshipType.RELATED,
    )
    
    # Connection strength (for visualization)
    strength: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        comment="Connection strength (0-1) for edge thickness",
    )
    
    # Optional metadata
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Why these are connected",
    )
    
    # Auto-generated or manual
    is_auto_generated: Mapped[bool] = mapped_column(
        default=False,
        comment="True if created by AI analysis",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    from_node: Mapped["KnowledgeNode"] = relationship(
        "KnowledgeNode",
        foreign_keys=[from_node_id],
        back_populates="outgoing_edges",
    )
    to_node: Mapped["KnowledgeNode"] = relationship(
        "KnowledgeNode",
        foreign_keys=[to_node_id],
        back_populates="incoming_edges",
    )
    
    def __repr__(self) -> str:
        return (
            f"<KnowledgeEdge(from={self.from_node_id}, to={self.to_node_id}, "
            f"type={self.relationship_type}, strength={self.strength})>"
        )
