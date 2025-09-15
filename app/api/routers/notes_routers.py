# app/api/routers/notes_routers.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.contracts.notes_dtos import NoteCreate, NoteOut, NoteBase
from app.schemas.models.users_models import User
from app.schemas.database import get_async_session
from app.utility.auth import get_current_user
# from app.api.repositories.notes_repositories import get_note_repository # Not needed directly in endpoints
from app.api.services.notes_services import get_note_service
# from app.api.repositories.notes_repositories import NoteRepository # Not needed directly in endpoints
from app.api.services.notes_services import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/search", response_model=List[NoteOut]) # Use NoteOut for consistent serialization
async def search_notes(
    q: str = Query(..., alias="q", min_length=2, description="Search term for title/description"),
    collection_id: int = None,
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"), # Reasonable limit
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
):
    """
    Search for notes belonging to the current user.

    Query Parameters:
    - q: The search term (required, min 2 chars).
    - collection_id: Filter by collection ID.
    - skip: Number of results to skip (for pagination).
    - limit: Maximum number of results to return (max 100).
    """
    # Call the service method
    notes = await note_service.search_user_notes(
        user_id=current_user.id,
        query=q,
        collection_id=collection_id,
    )

    # Apply pagination in-memory
    paginated_notes = notes[skip : skip + limit]

    return paginated_notes

@router.get("/", response_model=List[NoteOut])
async def list_notes(
    collection_id: int = None,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
    # note_repo: NoteRepository = Depends(get_note_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # note_service.note_repo = note_repo # Remove
    return await note_service.get_user_notes(current_user.id, collection_id)

@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
    # note_repo: NoteRepository = Depends(get_note_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # note_service.note_repo = note_repo # Remove
    return await note_service.get_user_note_by_id(current_user.id, note_id)

@router.post("/", response_model=NoteOut, status_code=201)
async def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
    # note_repo: NoteRepository = Depends(get_note_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # note_service.note_repo = note_repo # Remove
    return await note_service.create_note_for_user(current_user.id, note)

@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: int,
    note_update: NoteBase,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
    # note_repo: NoteRepository = Depends(get_note_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # note_service.note_repo = note_repo # Remove
    return await note_service.update_user_note(current_user.id, note_id, note_update)

@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service),
    # note_repo: NoteRepository = Depends(get_note_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # note_service.note_repo = note_repo # Remove
    await note_service.delete_user_note(current_user.id, note_id)
    return

