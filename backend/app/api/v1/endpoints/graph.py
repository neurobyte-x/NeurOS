"""
NeurOS 2.0 Knowledge Graph API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.knowledge_node import NodeType, MasteryLevel
from app.models.knowledge_edge import RelationshipType
from app.services import graph_service

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


class NodeCreate(BaseModel):
    label: str
    node_type: NodeType
    domain: Optional[str] = None
    description: Optional[str] = None
    entry_id: Optional[int] = None


class EdgeCreate(BaseModel):
    source_id: int
    target_id: int
    relationship_type: RelationshipType
    description: Optional[str] = None
    strength: float = 1.0


class MasteryUpdate(BaseModel):
    mastery_level: MasteryLevel


@router.get("")
async def get_knowledge_graph(
    domain: Optional[str] = Query(default=None),
    max_nodes: int = Query(default=100, ge=10, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's knowledge graph for visualization."""
    return await graph_service.get_knowledge_graph(
        db=db,
        user_id=current_user.id,
        domain=domain,
        max_nodes=max_nodes,
    )


@router.post("/nodes")
async def create_node(
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge node."""
    node = await graph_service.create_knowledge_node(
        db=db,
        user_id=current_user.id,
        label=data.label,
        node_type=data.node_type,
        domain=data.domain,
        description=data.description,
        entry_id=data.entry_id,
    )
    return {
        "id": node.id,
        "label": node.label,
        "node_type": node.node_type.value,
        "domain": node.domain,
        "mastery_level": node.mastery_level,
        "created_at": node.created_at.isoformat(),
    }


@router.post("/edges")
async def create_edge(
    data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new edge between knowledge nodes."""
    edge = await graph_service.create_knowledge_edge(
        db=db,
        source_id=data.source_id,
        target_id=data.target_id,
        relationship_type=data.relationship_type,
        description=data.description,
        strength=data.strength,
    )
    return {
        "id": edge.id,
        "source": edge.source_id,
        "target": edge.target_id,
        "relationship_type": edge.relationship_type.value,
        "strength": edge.strength,
    }


@router.patch("/nodes/{node_id}/mastery")
async def update_mastery(
    node_id: int,
    data: MasteryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update mastery level for a knowledge node."""
    node = await graph_service.update_node_mastery(
        db=db,
        node_id=node_id,
        mastery_level=data.mastery_level,
    )
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {
        "id": node.id,
        "mastery_level": node.mastery_level,
        "access_count": node.access_count,
    }


@router.get("/nodes/{node_id}/related")
async def get_related_nodes(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get nodes related to a specific node."""
    return await graph_service.get_related_nodes(db=db, node_id=node_id)


@router.get("/nodes/{node_id}/suggestions")
async def get_connection_suggestions(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get suggested connections for a node."""
    return await graph_service.suggest_connections(
        db=db,
        user_id=current_user.id,
        node_id=node_id,
    )


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge node and its edges."""
    success = await graph_service.delete_knowledge_node(
        db=db,
        node_id=node_id,
        user_id=current_user.id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {"message": "Node deleted successfully"}
