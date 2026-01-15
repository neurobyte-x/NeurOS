"""
NeurOS 2.0 Knowledge Graph Service
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge_node import KnowledgeNode, NodeType, MasteryLevel
from app.models.knowledge_edge import KnowledgeEdge, RelationshipType


async def get_knowledge_graph(
    db: AsyncSession,
    user_id: int,
    domain: Optional[str] = None,
    max_nodes: int = 100
) -> dict:
    """Get user's knowledge graph data for visualization."""
    # Build query for nodes
    query = select(KnowledgeNode).where(KnowledgeNode.user_id == user_id)
    
    if domain:
        query = query.where(KnowledgeNode.domain == domain)
    
    query = query.limit(max_nodes)
    
    result = await db.execute(query)
    nodes = result.scalars().all()
    
    node_ids = [n.id for n in nodes]
    
    # Get edges between these nodes
    if node_ids:
        edges_result = await db.execute(
            select(KnowledgeEdge).where(
                and_(
                    KnowledgeEdge.source_id.in_(node_ids),
                    KnowledgeEdge.target_id.in_(node_ids)
                )
            )
        )
        edges = edges_result.scalars().all()
    else:
        edges = []
    
    return {
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "node_type": n.node_type.value,
                "domain": n.domain,
                "mastery_level": n.mastery_level,
                "description": n.description,
                "access_count": n.access_count,
                "created_at": n.created_at.isoformat(),
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source_id,
                "target": e.target_id,
                "relationship_type": e.relationship_type.value,
                "strength": e.strength,
                "description": e.description,
            }
            for e in edges
        ],
        "statistics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "domains": list(set(n.domain for n in nodes if n.domain)),
        }
    }


async def create_knowledge_node(
    db: AsyncSession,
    user_id: int,
    label: str,
    node_type: NodeType,
    domain: Optional[str] = None,
    description: Optional[str] = None,
    entry_id: Optional[int] = None
) -> KnowledgeNode:
    """Create a new knowledge node."""
    node = KnowledgeNode(
        user_id=user_id,
        label=label,
        node_type=node_type,
        domain=domain,
        description=description,
        entry_id=entry_id,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


async def create_knowledge_edge(
    db: AsyncSession,
    source_id: int,
    target_id: int,
    relationship_type: RelationshipType,
    description: Optional[str] = None,
    strength: float = 1.0
) -> KnowledgeEdge:
    """Create a new edge between knowledge nodes."""
    edge = KnowledgeEdge(
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        description=description,
        strength=strength,
    )
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    return edge


async def update_node_mastery(
    db: AsyncSession,
    node_id: int,
    mastery_level: MasteryLevel
) -> Optional[KnowledgeNode]:
    """Update mastery level for a knowledge node."""
    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    
    if node:
        node.mastery_level = mastery_level
        node.access_count += 1
        node.last_accessed = datetime.utcnow()
        await db.commit()
        await db.refresh(node)
    
    return node


async def get_related_nodes(
    db: AsyncSession,
    node_id: int,
    relationship_types: Optional[list[RelationshipType]] = None
) -> list[dict]:
    """Get nodes related to a specific node."""
    query = select(KnowledgeEdge).where(
        (KnowledgeEdge.source_id == node_id) | (KnowledgeEdge.target_id == node_id)
    )
    
    if relationship_types:
        query = query.where(KnowledgeEdge.relationship_type.in_(relationship_types))
    
    result = await db.execute(query)
    edges = result.scalars().all()
    
    # Get related node IDs
    related_ids = set()
    for edge in edges:
        if edge.source_id == node_id:
            related_ids.add(edge.target_id)
        else:
            related_ids.add(edge.source_id)
    
    if not related_ids:
        return []
    
    nodes_result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id.in_(related_ids))
    )
    nodes = nodes_result.scalars().all()
    
    return [
        {
            "id": n.id,
            "label": n.label,
            "node_type": n.node_type.value,
            "domain": n.domain,
            "mastery_level": n.mastery_level,
        }
        for n in nodes
    ]


async def suggest_connections(
    db: AsyncSession,
    user_id: int,
    node_id: int
) -> list[dict]:
    """Suggest potential connections for a node based on domain and type."""
    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    
    if not node:
        return []
    
    # Find existing edges for this node
    existing_edges = await db.execute(
        select(KnowledgeEdge).where(
            (KnowledgeEdge.source_id == node_id) | (KnowledgeEdge.target_id == node_id)
        )
    )
    connected_ids = set()
    for edge in existing_edges.scalars().all():
        connected_ids.add(edge.source_id)
        connected_ids.add(edge.target_id)
    
    # Find similar nodes not yet connected
    suggestions_result = await db.execute(
        select(KnowledgeNode)
        .where(
            and_(
                KnowledgeNode.user_id == user_id,
                KnowledgeNode.id != node_id,
                ~KnowledgeNode.id.in_(connected_ids) if connected_ids else True,
                (KnowledgeNode.domain == node.domain) | (KnowledgeNode.node_type == node.node_type)
            )
        )
        .limit(10)
    )
    
    suggestions = suggestions_result.scalars().all()
    
    return [
        {
            "id": s.id,
            "label": s.label,
            "node_type": s.node_type.value,
            "domain": s.domain,
            "reason": "same_domain" if s.domain == node.domain else "same_type",
        }
        for s in suggestions
    ]


async def delete_knowledge_node(
    db: AsyncSession,
    node_id: int,
    user_id: int
) -> bool:
    """Delete a knowledge node and its edges."""
    result = await db.execute(
        select(KnowledgeNode).where(
            and_(
                KnowledgeNode.id == node_id,
                KnowledgeNode.user_id == user_id
            )
        )
    )
    node = result.scalar_one_or_none()
    
    if not node:
        return False
    
    # Delete edges
    await db.execute(
        KnowledgeEdge.__table__.delete().where(
            (KnowledgeEdge.source_id == node_id) | (KnowledgeEdge.target_id == node_id)
        )
    )
    
    # Delete node
    await db.delete(node)
    await db.commit()
    
    return True
