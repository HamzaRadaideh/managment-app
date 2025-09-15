# app/api/routers/collections_routers.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.contracts.collections_dtos import CollectionCreate, CollectionOut, CollectionWithItems
from app.schemas.models.users_models import User
from app.schemas.database import get_async_session
from app.utility.auth import get_current_user
# from app.api.repositories.collections_repositories import get_collection_repository # Not needed directly in endpoints
from app.api.services.collections_services import get_collection_service
# from app.api.repositories.collections_repositories import CollectionRepository # Not needed directly in endpoints
from app.api.services.collections_services import CollectionService

router = APIRouter(prefix="/collections", tags=["collections"])

@router.get("/search", response_model=List[CollectionOut]) # Use CollectionOut for consistent serialization
async def search_collections(
    q: str = Query(..., alias="q", min_length=2, description="Search term for collection title"),
    type: str = None, # Maps to CollectionType enum string value
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"), # Reasonable limit
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
):
    """
    Search for collections belonging to the current user.

    Query Parameters:
    - q: The search term (required, min 2 chars).
    - type: Filter by collection type (e.g., 'mixed', 'tasks-only', 'notes-only').
    - skip: Number of results to skip (for pagination).
    - limit: Maximum number of results to return (max 100).
    """
    # Call the service method
    collections = await collection_service.search_user_collections(
        user_id=current_user.id,
        query=q,
        type_filter=type, # Pass the type filter string
    )

    # Apply pagination in-memory
    paginated_collections = collections[skip : skip + limit]

    return paginated_collections

@router.get("/", response_model=List[CollectionOut])
async def list_collections(
    type: str = None,
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
    # collection_repo: CollectionRepository = Depends(get_collection_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # collection_service.collection_repo = collection_repo # Remove
    return await collection_service.get_user_collections(current_user.id, type)

@router.get("/{collection_id}", response_model=CollectionWithItems)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
    # collection_repo: CollectionRepository = Depends(get_collection_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # collection_service.collection_repo = collection_repo # Remove
    # Request to preload items
    return await collection_service.get_user_collection_by_id(
        current_user.id, collection_id, preload_items=True
    )

@router.post("/", response_model=CollectionOut, status_code=201)
async def create_collection(
    collection: CollectionCreate,
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
    # collection_repo: CollectionRepository = Depends(get_collection_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # collection_service.collection_repo = collection_repo # Remove
    return await collection_service.create_collection_for_user(current_user.id, collection)

@router.put("/{collection_id}", response_model=CollectionOut)
async def update_collection(
    collection_id: int,
    collection_update: CollectionCreate,
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
    # collection_repo: CollectionRepository = Depends(get_collection_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # collection_service.collection_repo = collection_repo # Remove
    return await collection_service.update_user_collection(
        current_user.id, collection_id, collection_update
    )

@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    collection_service: CollectionService = Depends(get_collection_service),
    # collection_repo: CollectionRepository = Depends(get_collection_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # collection_service.collection_repo = collection_repo # Remove
    await collection_service.delete_user_collection(current_user.id, collection_id)
    return

