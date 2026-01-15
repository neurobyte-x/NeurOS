"""
NeurOS 2.0 Knowledge Graph Schemas

Pydantic schemas for knowledge graph visualization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.knowledge_node import NodeType
from app.models.knowledge_edge import RelationshipType


class KnowledgeNodeBase(BaseModel):
    """Base schema for knowledge nodes."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    node_type: NodeType = NodeType.CONCEPT
    domain: Optional[str] = None


class KnowledgeNodeCreate(KnowledgeNodeBase):
    """Schema for creating a knowledge node."""
    linked_pattern_id: Optional[int] = None
    linked_entry_id: Optional[int] = None


class KnowledgeNodeUpdate(BaseModel):
    """Schema for updating a knowledge node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    node_type: Optional[NodeType] = None
    domain: Optional[str] = None
    mastery_level: Optional[int] = Field(None, ge=1, le=5)


class KnowledgeNodeResponse(KnowledgeNodeBase):
    """Schema for knowledge node response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    mastery_level: int
    decay_score: int
    last_practiced_at: Optional[datetime]
    times_practiced: int
    linked_pattern_id: Optional[int]
    linked_entry_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    color_indicator: str = "green"
    size_factor: float = 1.0


class KnowledgeEdgeBase(BaseModel):
    """Base schema for knowledge edges."""
    from_node_id: int
    to_node_id: int
    relationship_type: RelationshipType = RelationshipType.RELATED
    strength: float = Field(0.5, ge=0, le=1)
    description: Optional[str] = None


class KnowledgeEdgeCreate(KnowledgeEdgeBase):
    """Schema for creating a knowledge edge."""
    pass


class KnowledgeEdgeResponse(KnowledgeEdgeBase):
    """Schema for knowledge edge response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_auto_generated: bool
    created_at: datetime


class GraphNode(BaseModel):
    """Node formatted for D3.js visualization."""
    id: int
    name: str
    type: str
    domain: Optional[str]
    color: str
    size: float
    decay_score: int
    mastery_level: int
    is_clickable: bool = True
    tooltip: str


class GraphEdge(BaseModel):
    """Edge formatted for D3.js visualization."""
    id: int
    source: int
    target: int
    type: str
    width: float
    label: Optional[str]


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph for visualization."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int
    domains: list[str]
    average_mastery: float
    average_decay: float
    isolated_nodes: int


class GraphFilter(BaseModel):
    """Filter options for graph visualization."""
    domains: Optional[list[str]] = None
    node_types: Optional[list[NodeType]] = None
    min_mastery: Optional[int] = None
    max_decay: Optional[int] = None
    show_isolated: bool = True
    depth: int = Field(3, ge=1, le=10)
