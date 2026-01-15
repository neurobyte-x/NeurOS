"""
NeurOS 2.0 Patterns API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pattern_service import PatternService
from app.services.entry_service import EntryService
from app.schemas.pattern import (
    PatternCreate, PatternUpdate, PatternResponse,
    PatternWithTemplates, PatternListResponse,
    PatternTemplateCreate, PatternTemplateResponse,
)
from app.dependencies import CurrentUser

router = APIRouter(prefix="/patterns", tags=["Patterns"])


@router.post("", response_model=PatternResponse, status_code=status.HTTP_201_CREATED)
async def create_pattern(
    data: PatternCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new thinking pattern."""
    service = PatternService(db)
    return await service.create_pattern(current_user.id, data)


@router.get("", response_model=PatternListResponse)
async def list_patterns(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: str | None = None,
):
    """List patterns with optional domain filter."""
    service = PatternService(db)
    patterns, total = await service.get_patterns(current_user.id, domain, page, page_size)
    
    return PatternListResponse(
        items=patterns,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/search")
async def search_patterns(
    query: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Search patterns by name."""
    service = PatternService(db)
    return await service.search_patterns(current_user.id, query)


@router.get("/cross-domain", response_model=list[PatternResponse])
async def get_cross_domain_patterns(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get patterns used across multiple domains."""
    service = PatternService(db)
    return await service.get_cross_domain_patterns(current_user.id)


@router.get("/{pattern_id}", response_model=PatternWithTemplates)
async def get_pattern(
    pattern_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get pattern by ID with templates."""
    service = PatternService(db)
    pattern = await service.get_pattern(pattern_id, current_user.id)
    
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    
    return pattern


@router.patch("/{pattern_id}", response_model=PatternResponse)
async def update_pattern(
    pattern_id: int,
    data: PatternUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update a pattern."""
    service = PatternService(db)
    pattern = await service.get_pattern(pattern_id, current_user.id)
    
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    
    return await service.update_pattern(pattern, data)


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pattern(
    pattern_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete a pattern."""
    service = PatternService(db)
    pattern = await service.get_pattern(pattern_id, current_user.id)
    
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    
    await service.delete_pattern(pattern)


@router.post("/{pattern_id}/templates", response_model=PatternTemplateResponse)
async def add_template(
    pattern_id: int,
    data: PatternTemplateCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Add a code template to a pattern."""
    service = PatternService(db)
    pattern = await service.get_pattern(pattern_id, current_user.id)
    
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    
    return await service.add_template(pattern, data)


@router.post("/{pattern_id}/link/{entry_id}")
async def link_pattern_to_entry(
    pattern_id: int,
    entry_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    was_successful: bool = True,
):
    """Link a pattern to an entry."""
    pattern_service = PatternService(db)
    entry_service = EntryService(db)
    
    pattern = await pattern_service.get_pattern(pattern_id, current_user.id)
    if not pattern:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    
    entry = await entry_service.get_entry(entry_id, current_user.id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    await pattern_service.link_pattern_to_entry(pattern, entry, was_successful)
    return {"message": "Pattern linked to entry"}
