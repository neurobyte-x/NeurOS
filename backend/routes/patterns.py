"""
Pattern routes - API endpoints for thinking patterns.

WHY: Patterns are the reusable knowledge units.
These endpoints support pattern CRUD and discovery.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.pattern import (
    PatternCreate, PatternUpdate, PatternResponse,
    PatternWithEntries
)
from services.pattern_service import PatternService

router = APIRouter()


@router.post("/", response_model=PatternResponse, status_code=201)
def create_pattern(
    pattern_data: PatternCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user-defined pattern.
    
    WHY: Patterns should be in YOUR words, not textbook terms.
    "pointer dance" > "two pointer technique" if that's how you think.
    """
    service = PatternService(db)
    
    try:
        pattern = service.create_pattern(pattern_data)
        return pattern
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/", response_model=List[PatternResponse])
def list_patterns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    domain: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("usage_count", regex="^(usage_count|name|created_at)$"),
    db: Session = Depends(get_db)
):
    """
    List all patterns with filters.
    
    WHY: Browse your pattern vocabulary. Sort by usage
    to see which patterns appear most often.
    """
    service = PatternService(db)
    patterns, total = service.get_patterns(
        page=page,
        page_size=page_size,
        domain_tag=domain,
        search_query=search,
        sort_by=sort_by,
    )
    return patterns


@router.get("/cross-domain", response_model=List[PatternResponse])
def get_cross_domain_patterns(db: Session = Depends(get_db)):
    """
    Get patterns that appear across multiple domains.
    
    WHY: These are your most valuable, transferable patterns.
    "State compression" in DSA vs "Caching" in Backend - same idea!
    """
    service = PatternService(db)
    return service.get_cross_domain_patterns()


@router.get("/stats")
def get_pattern_stats(db: Session = Depends(get_db)):
    """Get aggregate pattern statistics."""
    service = PatternService(db)
    return service.get_pattern_stats()


@router.get("/search")
def search_patterns(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search patterns by name or description.
    
    WHY: Quick pattern lookup during entry creation.
    """
    service = PatternService(db)
    patterns, _ = service.get_patterns(
        page=1,
        page_size=limit,
        search_query=q,
    )
    return patterns


@router.get("/{pattern_id}", response_model=PatternWithEntries)
def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """
    Get pattern with all associated entries.
    
    WHY: See all instances where this pattern appeared.
    Great for revision and deepening understanding.
    """
    service = PatternService(db)
    pattern = service.get_pattern_with_entries(pattern_id)
    
    if not pattern:
        raise HTTPException(404, "Pattern not found")
    
    entries = [
        {
            "id": ep.entry.id,
            "title": ep.entry.title,
            "entry_type": ep.entry.entry_type.value,
            "created_at": ep.entry.created_at,
            "relevance_score": ep.relevance_score,
        }
        for ep in pattern.entries
    ]
    
    return {
        **PatternResponse.model_validate(pattern).model_dump(),
        "entries": entries,
    }


@router.put("/{pattern_id}", response_model=PatternResponse)
def update_pattern(
    pattern_id: int,
    pattern_data: PatternUpdate,
    db: Session = Depends(get_db)
):
    """Update a pattern."""
    service = PatternService(db)
    
    try:
        pattern = service.update_pattern(pattern_id, pattern_data)
        if not pattern:
            raise HTTPException(404, "Pattern not found")
        return pattern
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{pattern_id}")
def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """Delete a pattern."""
    service = PatternService(db)
    success = service.delete_pattern(pattern_id)
    
    if not success:
        raise HTTPException(404, "Pattern not found")
    
    return {"message": "Pattern deleted"}


@router.post("/{pattern_id}/merge/{target_id}")
def merge_patterns(
    pattern_id: int,
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Merge one pattern into another.
    
    WHY: Sometimes you realize two patterns are the same thing.
    Merge them to consolidate your vocabulary.
    """
    service = PatternService(db)
    
    source = service.get_pattern(pattern_id)
    target = service.get_pattern(target_id)
    
    if not source or not target:
        raise HTTPException(404, "One or both patterns not found")
    
    if source.id == target.id:
        raise HTTPException(400, "Cannot merge pattern with itself")
    
    from models import EntryPattern
    associations = db.query(EntryPattern).filter(
        EntryPattern.pattern_id == source.id
    ).all()
    
    for assoc in associations:
        assoc.pattern_id = target.id
    
    target.usage_count += source.usage_count
    
    if source.domain_tags:
        source_tags = set(source.domain_tags.split(","))
        target_tags = set((target.domain_tags or "").split(","))
        merged_tags = source_tags | target_tags
        target.domain_tags = ",".join(t for t in merged_tags if t)
    
    db.delete(source)
    db.commit()
    
    return {
        "message": f"Merged '{source.name}' into '{target.name}'",
        "target_id": target.id,
    }
