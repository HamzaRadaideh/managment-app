# app/api/routers/tags_routers.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.contracts.tags_dtos import TagCreate, TagOut
from app.schemas.models.users_models import User
from app.schemas.database import get_async_session
from app.utility.auth import get_current_user
# from app.api.repositories.tags_repositories import get_tag_repository # Not needed directly in endpoints
from app.api.services.tags_services import get_tag_service
# from app.api.repositories.tags_repositories import TagRepository # Not needed directly in endpoints
from app.api.services.tags_services import TagService

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/search", response_model=List[TagOut]) # Use TagOut for consistent serialization
async def search_tags(
    q: str = Query(..., alias="q", min_length=2, description="Search term for tag title"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"), # Reasonable limit
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
):
    """
    Search for tags belonging to the current user.

    Query Parameters:
    - q: The search term (required, min 2 chars).
    - skip: Number of results to skip (for pagination).
    - limit: Maximum number of results to return (max 100).
    """
    # Call the service method
    tags = await tag_service.search_user_tags(
        user_id=current_user.id,
        query=q,
    )

    # Apply pagination in-memory
    paginated_tags = tags[skip : skip + limit]

    return paginated_tags

@router.get("/", response_model=List[TagOut])
async def list_tags(
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
    # tag_repo: TagRepository = Depends(get_tag_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # tag_service.tag_repo = tag_repo # Remove
    return await tag_service.get_user_tags(current_user.id)

@router.get("/{tag_id}", response_model=TagOut)
async def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
    # tag_repo: TagRepository = Depends(get_tag_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # tag_service.tag_repo = tag_repo # Remove
    return await tag_service.get_user_tag_by_id(current_user.id, tag_id)

@router.post("/", response_model=TagOut, status_code=201)
async def create_tag(
    tag: TagCreate,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
    # tag_repo: TagRepository = Depends(get_tag_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # tag_service.tag_repo = tag_repo # Remove
    return await tag_service.create_tag_for_user(current_user.id, tag)

@router.put("/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: int,
    tag_update: TagCreate,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
    # tag_repo: TagRepository = Depends(get_tag_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # tag_service.tag_repo = tag_repo # Remove
    return await tag_service.update_user_tag(current_user.id, tag_id, tag_update)

@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    tag_service: TagService = Depends(get_tag_service),
    # tag_repo: TagRepository = Depends(get_tag_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # tag_service.tag_repo = tag_repo # Remove
    await tag_service.delete_user_tag(current_user.id, tag_id)
    return

