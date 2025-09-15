# app/api/services/search_services.py
import asyncio
from typing import Dict, Any, List # Add List
from fastapi import Depends, HTTPException, status

# Import services we depend on
from app.api.services.tasks_services import TaskService, get_task_service
from app.api.services.notes_services import NoteService, get_note_service
from app.api.services.collections_services import CollectionService, get_collection_service
from app.api.services.tags_services import TagService, get_tag_service

# Import DTOs for serialization (This is the key addition!)
from app.schemas.contracts.tasks_dtos import TaskOut
from app.schemas.contracts.notes_dtos import NoteOut
from app.schemas.contracts.collections_dtos import CollectionOut
from app.schemas.contracts.tags_dtos import TagOut

# Import ORM models if needed for isinstance checks (optional here, but good practice if logic gets complex)
# from app.schemas.models.tasks_models import Task
# from app.schemas.models.notes_models import Note
# from app.schemas.models.collections_models import Collection
# from app.schemas.models.tags_models import Tag

class SearchService:
    """
    Service to perform a global search across Tasks, Notes, Collections, and Tags.
    """

    def __init__(
        self,
        task_service: TaskService,
        note_service: NoteService,
        collection_service: CollectionService,
        tag_service: TagService,
    ):
        self.task_service = task_service
        self.note_service = note_service
        self.collection_service = collection_service
        self.tag_service = tag_service

    async def global_search(
        self, user_id: int, query: str, limit_per_type: int = 20
    ) -> Dict[str, Any]:
        """
        Perform a global search across tasks, notes, collections, and tags for a user.

        Args:
            user_id: The ID of the authenticated user.
            query: The search term.
            limit_per_type: Maximum number of results to return per entity type.

        Returns:
            A dictionary containing the search results and metadata.
        """
        # Basic validation
        if not query or len(query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long."
            )

        stripped_query = query.strip()

        tasks_results, notes_results, collections_results, tags_results = await asyncio.gather(
            self.task_service.search_user_tasks(user_id, stripped_query, None, None, None),
            self.note_service.search_user_notes(user_id, stripped_query, None),
            self.collection_service.search_user_collections(user_id, stripped_query, None),
            self.tag_service.search_user_tags(user_id, stripped_query),
        )

        # --- Apply limit per type ---
        limited_tasks_orm = tasks_results[:limit_per_type]
        limited_notes_orm = notes_results[:limit_per_type]
        limited_collections_orm = collections_results[:limit_per_type]
        limited_tags_orm = tags_results[:limit_per_type]

        # --- Convert ORM objects to DTOs for serialization ---
        # This is the crucial step that was missing!
        limited_tasks_dto = [TaskOut.model_validate(task) for task in limited_tasks_orm]
        limited_notes_dto = [NoteOut.model_validate(note) for note in limited_notes_orm]
        limited_collections_dto = [CollectionOut.model_validate(collection) for collection in limited_collections_orm]
        limited_tags_dto = [TagOut.model_validate(tag) for tag in limited_tags_orm]

        # --- Calculate total count ---
        total_count = (
            len(tasks_results) +
            len(notes_results) +
            len(collections_results) +
            len(tags_results)
        )

        # --- Construct the response with DTOs ---
        return {
            "query": stripped_query,
            "results": {
                "tasks": limited_tasks_dto,        # Use DTOs
                "notes": limited_notes_dto,        # Use DTOs
                "collections": limited_collections_dto, # Use DTOs
                "tags": limited_tags_dto,          # Use DTOs
            },
            "total_count": total_count,
            # Future hook for relevance scores (if added later)
            # "relevance_scores": { ... }
        }

# Dependency function to inject the SearchService
def get_search_service(
    task_service: TaskService = Depends(get_task_service),
    note_service: NoteService = Depends(get_note_service),
    collection_service: CollectionService = Depends(get_collection_service),
    tag_service: TagService = Depends(get_tag_service),
) -> SearchService:
    """
    Dependency function to create and provide a SearchService instance.
    """
    return SearchService(
        task_service=task_service,
        note_service=note_service,
        collection_service=collection_service,
        tag_service=tag_service,
    )
