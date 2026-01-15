"""
NeurOS 2.0 Entries API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.entry_service import EntryService
from app.schemas.entry import (
    EntryCreate, EntryUpdate, EntryResponse, EntryListResponse,
    EntryFilter, ReflectionCreate,
)
from app.dependencies import CurrentUser
from app.models.entry import EntryType, DifficultyLevel

router = APIRouter(prefix="/entries", tags=["Entries"])


@router.post("", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    data: EntryCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new learning entry."""
    service = EntryService(db)
    return await service.create_entry(current_user.id, data)


@router.get("", response_model=EntryListResponse)
async def list_entries(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entry_type: EntryType | None = None,
    is_completed: bool | None = None,
    difficulty: DifficultyLevel | None = None,
    search: str | None = None,
):
    """List entries with filters and pagination."""
    service = EntryService(db)
    
    filters = EntryFilter(
        entry_type=entry_type,
        is_completed=is_completed,
        difficulty=difficulty,
        search=search,
    )
    
    entries, total = await service.get_entries(
        current_user.id, filters, page, page_size
    )
    
    return EntryListResponse(
        items=entries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get entry by ID."""
    service = EntryService(db)
    entry = await service.get_entry(entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    return entry


@router.patch("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: int,
    data: EntryUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update an entry."""
    service = EntryService(db)
    entry = await service.get_entry(entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    return await service.update_entry(entry, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete an entry."""
    service = EntryService(db)
    entry = await service.get_entry(entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    await service.delete_entry(entry)


@router.post("/{entry_id}/reflection", response_model=EntryResponse)
async def add_reflection(
    entry_id: int,
    data: ReflectionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Add reflection to entry (marks it as completed)."""
    service = EntryService(db)
    entry = await service.get_entry(entry_id, current_user.id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    if entry.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entry already has a reflection",
        )
    
    return await service.add_reflection(entry, data)
