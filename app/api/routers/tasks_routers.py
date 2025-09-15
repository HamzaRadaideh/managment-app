# app/api/routers/tasks_routers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.schemas.contracts.tasks_dtos import TaskCreate, TaskOut, TaskBase
from app.schemas.models.users_models import User
from app.schemas.database import get_async_session
from app.utility.auth import get_current_user
# from app.api.repositories.tasks_repositories import get_task_repository # Not needed directly in endpoints
from app.api.services.tasks_services import get_task_service
# from app.api.repositories.tasks_repositories import TaskRepository # Not needed directly in endpoints
from app.api.services.tasks_services import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/search", response_model=List[TaskOut]) # Use TaskOut for consistent serialization
async def search_tasks(
    q: str = Query(..., alias="q", min_length=2, description="Search term for title/description"),
    status: str = None,
    priority: str = None,
    collection_id: int = None,
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"), # Reasonable limit
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """
    Search for tasks belonging to the current user.

    Query Parameters:
    - q: The search term (required, min 2 chars).
    - status: Filter by task status.
    - priority: Filter by task priority.
    - collection_id: Filter by collection ID.
    - skip: Number of results to skip (for pagination).
    - limit: Maximum number of results to return (max 100).
    """
    # Call the service method
    tasks = await task_service.search_user_tasks(
        user_id=current_user.id,
        query=q,
        status=status,
        priority=priority,
        collection_id=collection_id,
    )

    # Apply pagination in-memory (as suggested in the plan)
    # This is because complex ordering combined with LIKE can make DB-level pagination tricky.
    paginated_tasks = tasks[skip : skip + limit]

    return paginated_tasks



@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    status: str = None,
    priority: str = None,
    collection_id: int = None,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    # task_repo: TaskRepository = Depends(get_task_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # task_service.task_repo = task_repo # Remove
    return await task_service.get_user_tasks(
        current_user.id, status, priority, collection_id
    )

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    # task_repo: TaskRepository = Depends(get_task_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # task_service.task_repo = task_repo # Remove
    return await task_service.get_user_task_by_id(current_user.id, task_id)

@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    # task_repo: TaskRepository = Depends(get_task_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # task_service.task_repo = task_repo # Remove
    return await task_service.create_task_for_user(current_user.id, task)

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    task_update: TaskBase,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    # task_repo: TaskRepository = Depends(get_task_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # task_service.task_repo = task_repo # Remove
    return await task_service.update_user_task(
        current_user.id, task_id, task_update
    )

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    # task_repo: TaskRepository = Depends(get_task_repository), # Remove
    # db: AsyncSession = Depends(get_async_session) # Not needed if service handles persistence
):
    # task_service.task_repo = task_repo # Remove
    await task_service.delete_user_task(current_user.id, task_id)
    return

