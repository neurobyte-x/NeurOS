"""
Recall routes - intelligence layer API.

WHY: The recall system is what makes Thinking OS smart.
These endpoints surface relevant history before new work.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.entry import EntryType
from schemas.analytics import RecallContext, RecallResponse
from services.recall_service import RecallService

router = APIRouter()


@router.post("/context", response_model=RecallResponse)
def get_recall_context(
    context: RecallContext,
    db: Session = Depends(get_db)
):
    """
    Get full recall context before starting new work.
    
    WHY: This is THE intelligence endpoint. Before diving into
    a new problem, call this to get:
    - Similar past entries
    - Relevant patterns
    - Blocker warnings
    - Revision suggestions
    
    Use this to learn from your past self.
    """
    service = RecallService(db)
    
    # Parse entry type
    entry_type = None
    if context.entry_type:
        try:
            entry_type = EntryType(context.entry_type)
        except ValueError:
            pass
    
    result = service.get_full_recall_context(
        title=context.title,
        entry_type=entry_type,
        description=context.description,
        keywords=context.keywords,
    )
    
    return result


@router.get("/similar")
def get_similar_entries(
    title: Optional[str] = None,
    entry_type: Optional[str] = None,
    keywords: Optional[str] = None,  # Comma-separated
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Find similar past entries.
    
    WHY: Quick similarity check. "Have I solved this before?"
    """
    service = RecallService(db)
    
    type_enum = None
    if entry_type:
        try:
            type_enum = EntryType(entry_type)
        except ValueError:
            pass
    
    keyword_list = None
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(",")]
    
    return service.get_similar_entries(
        title=title,
        entry_type=type_enum,
        keywords=keyword_list,
        limit=limit,
    )


@router.get("/patterns")
def get_relevant_patterns(
    title: Optional[str] = None,
    entry_type: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get patterns that might be relevant.
    
    WHY: Pattern suggestions help you apply past learnings.
    """
    service = RecallService(db)
    
    type_enum = None
    if entry_type:
        try:
            type_enum = EntryType(entry_type)
        except ValueError:
            pass
    
    keyword_list = None
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(",")]
    
    return service.get_relevant_patterns(
        title=title,
        entry_type=type_enum,
        keywords=keyword_list,
        limit=limit,
    )


@router.get("/blockers")
def get_blocker_warnings(
    context: Optional[str] = None,
    entry_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get warnings about repeated blockers.
    
    WHY: "You've struggled with X three times" is powerful
    feedback for focusing improvement.
    """
    service = RecallService(db)
    
    type_enum = None
    if entry_type:
        try:
            type_enum = EntryType(entry_type)
        except ValueError:
            pass
    
    return service.get_blocker_warnings(context, type_enum)


@router.get("/revisions")
def get_revision_suggestions(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get items that need revision.
    
    WHY: Spaced repetition recommendations based on
    confidence levels and time since last review.
    """
    service = RecallService(db)
    return service.get_revision_suggestions(limit)
