"""
Entry routes - API endpoints for learning entries.

WHY: RESTful API for entry management with
reflection enforcement built into the workflow.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Entry, Reflection, EntryType
from schemas.entry import (
    EntryCreate, EntryUpdate, EntryResponse,
    EntryWithReflection, EntryListResponse
)
from schemas.reflection import ReflectionCreate, ReflectionResponse
from services.entry_service import EntryService
from services.pattern_service import PatternService
from services.recall_service import RecallService

router = APIRouter()


@router.post("/", response_model=EntryResponse, status_code=201)
def create_entry(
    entry_data: EntryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new learning entry.
    
    WHY: Entry starts incomplete. You MUST add reflection
    via POST /entries/{id}/reflection to complete it.
    
    This enforces the "reflection before persistence" philosophy.
    """
    service = EntryService(db)
    entry = service.create_entry(entry_data)
    return entry


@router.get("/", response_model=EntryListResponse)
def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entry_type: Optional[str] = None,
    is_complete: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List entries with pagination and filters.
    
    WHY: Support browsing and filtering for revision sessions.
    """
    service = EntryService(db)
    
    type_enum = None
    if entry_type:
        try:
            type_enum = EntryType(entry_type)
        except ValueError:
            raise HTTPException(400, f"Invalid entry type: {entry_type}")
    
    entries, total = service.get_entries(
        page=page,
        page_size=page_size,
        entry_type=type_enum,
        is_complete=is_complete,
        search_query=search,
    )
    
    return EntryListResponse(
        entries=entries,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/incomplete", response_model=List[EntryResponse])
def list_incomplete_entries(db: Session = Depends(get_db)):
    """
    Get all incomplete entries (awaiting reflection).
    
    WHY: Dashboard reminder of what needs reflection.
    Encourages completing the learning loop.
    """
    service = EntryService(db)
    return service.get_incomplete_entries()


@router.get("/search", response_model=List[EntryWithReflection])
def search_entries(
    q: str = Query(..., min_length=1),
    entry_types: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search entries by keyword.
    
    WHY: Find past entries by memory fragments.
    Searches title, reflection context, and patterns.
    """
    service = EntryService(db)
    
    type_list = None
    if entry_types:
        type_list = [EntryType(t.strip()) for t in entry_types.split(",")]
    
    entries = service.search_entries(q, type_list, limit)
    
    results = []
    for entry in entries:
        result = EntryWithReflection.model_validate(entry)
        results.append(result)
    
    return results


@router.get("/stats")
def get_entry_stats(db: Session = Depends(get_db)):
    """Get aggregate entry statistics."""
    service = EntryService(db)
    return service.get_entry_stats()


@router.get("/{entry_id}", response_model=EntryWithReflection)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    """
    Get a single entry with full details.
    
    WHY: Includes reflection and patterns for complete view.
    """
    service = EntryService(db)
    entry = service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    response_data = {
        "id": entry.id,
        "title": entry.title,
        "entry_type": entry.entry_type,
        "source_url": entry.source_url,
        "source_name": entry.source_name,
        "difficulty": entry.difficulty,
        "time_spent_minutes": entry.time_spent_minutes,
        "code_snippet": entry.code_snippet,
        "language": entry.language,
        "is_complete": entry.is_complete,
        "has_reflection": entry.has_reflection,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "reflection": entry.reflection,
        "patterns": [
            {
                "id": ep.pattern.id,
                "name": ep.pattern.name,
                "description": ep.pattern.description,
                "relevance_score": ep.relevance_score,
            }
            for ep in entry.patterns
        ]
    }
    
    return response_data


@router.put("/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: int,
    entry_data: EntryUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing entry."""
    service = EntryService(db)
    entry = service.update_entry(entry_id, entry_data)
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    return entry


@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete an entry and all related data."""
    service = EntryService(db)
    success = service.delete_entry(entry_id)
    
    if not success:
        raise HTTPException(404, "Entry not found")
    
    return {"message": "Entry deleted"}


@router.post("/{entry_id}/reflection", response_model=EntryWithReflection)
def add_reflection(
    entry_id: int,
    reflection_data: ReflectionCreate,
    db: Session = Depends(get_db)
):
    """
    Add reflection to an entry (REQUIRED to complete entry).
    
    WHY: This is THE key endpoint. An entry without reflection
    is incomplete and doesn't count toward your learning record.
    
    All mandatory fields are validated:
    - context: What were you solving?
    - initial_blocker: Why were you stuck?
    - trigger_signal: What revealed the solution?
    - key_pattern: Name the pattern
    - mistake_or_edge_case: What to remember
    
    Incomplete reflection → 422 error.
    """
    if reflection_data.entry_id != entry_id:
        raise HTTPException(400, "Entry ID mismatch")
    
    entry_service = EntryService(db)
    recall_service = RecallService(db)
    
    entry = entry_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    if entry.reflection:
        raise HTTPException(400, "Entry already has reflection. Use PUT to update.")
    
    reflection = Reflection(
        entry_id=entry_id,
        context=reflection_data.context,
        initial_blocker=reflection_data.initial_blocker,
        trigger_signal=reflection_data.trigger_signal,
        key_pattern=reflection_data.key_pattern,
        mistake_or_edge_case=reflection_data.mistake_or_edge_case,
        time_to_insight_minutes=reflection_data.time_to_insight_minutes,
        additional_notes=reflection_data.additional_notes,
        next_time_strategy=reflection_data.next_time_strategy,
        confidence_level=reflection_data.confidence_level,
    )
    
    if not reflection.is_complete():
        raise HTTPException(
            422, 
            "Reflection incomplete. All mandatory fields must be non-empty: "
            "context, initial_blocker, trigger_signal, key_pattern, mistake_or_edge_case"
        )
    
    entry = entry_service.add_reflection(entry_id, reflection)
    
    recall_service.record_blocker(entry_id, reflection_data.initial_blocker)
    
    pattern_service = PatternService(db)
    try:
        pattern = pattern_service.get_or_create_pattern(reflection_data.key_pattern)
        pattern_service.associate_pattern_with_entry(entry_id, pattern.id)
    except Exception:
        pass
    
    return entry_service.get_entry(entry_id)


@router.put("/{entry_id}/reflection", response_model=ReflectionResponse)
def update_reflection(
    entry_id: int,
    reflection_data: ReflectionCreate,
    db: Session = Depends(get_db)
):
    """Update an existing reflection."""
    entry_service = EntryService(db)
    entry = entry_service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    if not entry.reflection:
        raise HTTPException(400, "Entry has no reflection. Use POST to create.")
    
    reflection = entry.reflection
    reflection.context = reflection_data.context
    reflection.initial_blocker = reflection_data.initial_blocker
    reflection.trigger_signal = reflection_data.trigger_signal
    reflection.key_pattern = reflection_data.key_pattern
    reflection.mistake_or_edge_case = reflection_data.mistake_or_edge_case
    reflection.time_to_insight_minutes = reflection_data.time_to_insight_minutes
    reflection.additional_notes = reflection_data.additional_notes
    reflection.next_time_strategy = reflection_data.next_time_strategy
    reflection.confidence_level = reflection_data.confidence_level
    
    db.commit()
    db.refresh(reflection)
    
    return reflection


@router.post("/{entry_id}/patterns/{pattern_id}")
def associate_pattern(
    entry_id: int,
    pattern_id: int,
    relevance_score: float = Query(1.0, ge=0.0, le=1.0),
    application_notes: Optional[str] = None,
    was_successful: int = Query(1, ge=-1, le=1),
    db: Session = Depends(get_db)
):
    """
    Associate a pattern with an entry.
    
    WHY: One entry can demonstrate multiple patterns.
    This builds the knowledge graph for better recall.
    """
    entry_service = EntryService(db)
    pattern_service = PatternService(db)
    
    entry = entry_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    pattern = pattern_service.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(404, "Pattern not found")
    
    entry_pattern = pattern_service.associate_pattern_with_entry(
        entry_id=entry_id,
        pattern_id=pattern_id,
        relevance_score=relevance_score,
        application_notes=application_notes,
        was_successful=was_successful,
    )
    
    return {"message": "Pattern associated", "entry_pattern_id": entry_pattern.id}
