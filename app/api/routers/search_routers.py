# app/api/routers/search_routers.py
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

# Import models/user for auth
from app.schemas.models.users_models import User
from app.utility.auth import get_current_user

# Import the new service and its dependency
from app.api.services.search_services import SearchService, get_search_service

# Create the router with a prefix and tags
router = APIRouter(prefix="/search", tags=["search"])

@router.get("/global", response_model=Dict[str, Any]) # Basic dict response for now
async def global_search(
    q: str = Query(..., alias="q", min_length=2, description="Global search term"),
    limit: int = Query(20, ge=1, le=100, description="Max results per entity type (default 20)"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    """
    Perform a global search across Tasks, Notes, Collections, and Tags for the current user.

    Query Parameters:
    - q: The search term (required, min 2 chars).
    - limit: Maximum number of results to return per entity type (max 100, default 20).
    """
    results = await search_service.global_search(
        user_id=current_user.id,
        query=q,
        limit_per_type=limit
    )
    return results
