# app/api/services/collections_services.py
from fastapi import Depends, HTTPException, status
from typing import Optional
from app.api.repositories.collections_repositories import (
    CollectionRepository,
    get_collection_repository,
)
from app.schemas.models.collections_models import Collection
from app.schemas.contracts.collections_dtos import CollectionCreate


class CollectionService:
    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def get_user_collections(
        self, user_id: int, type_filter: str | None = None
    ) -> list[Collection]:
        return await self.collection_repo.get_collections_by_user(user_id, type_filter)

    async def get_user_collection_by_id(
        self, user_id: int, collection_id: int, preload_items: bool = False
    ) -> Collection:
        collection = await self.collection_repo.get_collection_by_id_and_user(
            collection_id, user_id
        )
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        if preload_items:
            await self.collection_repo.preload_collection_items(collection)

        return collection

    async def create_collection_for_user(
        self, user_id: int, collection_create: CollectionCreate
    ) -> Collection:
        existing = await self.collection_repo.get_collection_by_title_and_user(
            collection_create.title, user_id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Collection with this title already exists for the user",
            )

        data = collection_create.dict()
        tag_ids = data.pop("tag_ids", None)
        data["user_id"] = user_id

        if tag_ids is not None:
            found = await self.collection_repo.get_tags_by_ids_and_user(tag_ids, user_id)
            if len(found) != len(set(tag_ids)):
                found_ids = {t.id for t in found}
                missing = sorted(set(tag_ids) - found_ids)
                raise HTTPException(
                    status_code=400,
                    detail=f"Tags not found or not owned by user: {missing}",
                )

        new_collection = await self.collection_repo.create_collection(data)

        if tag_ids is not None:
            await self.collection_repo.set_collection_tags(new_collection, tag_ids)

        await self.collection_repo.db.commit()
        # Full refresh (grabs updated_at) + ensure tags are loaded
        await self.collection_repo.db.refresh(new_collection)
        await self.collection_repo.db.refresh(new_collection, attribute_names=["tags"])
        return new_collection

    async def update_user_collection(
        self, user_id: int, collection_id: int, collection_update: CollectionCreate
    ) -> Collection:
        collection = await self.get_user_collection_by_id(user_id, collection_id)

        if collection_update.title != collection.title:
            dup = await self.collection_repo.get_collection_by_title_and_user(
                collection_update.title, user_id
            )
            if dup:
                raise HTTPException(
                    status_code=400,
                    detail="Collection with this title already exists for the user",
                )

        update_data = collection_update.dict(exclude_unset=True)
        tag_ids_to_set = update_data.pop("tag_ids", None)

        await self.collection_repo.update_collection(collection, update_data)

        if tag_ids_to_set is not None:
            await self.collection_repo.set_collection_tags(collection, tag_ids_to_set)

        await self.collection_repo.db.commit()
        # Full refresh + tags loaded so serialization never lazy-loads
        await self.collection_repo.db.refresh(collection)
        await self.collection_repo.db.refresh(collection, attribute_names=["tags"])
        return collection

    async def delete_user_collection(self, user_id: int, collection_id: int) -> None:
        # Ensure the collection exists and belongs to the user
        collection = await self.get_user_collection_by_id(user_id, collection_id)
        # Deleting the collection will cascade to tasks/notes due to the model relationship config
        await self.collection_repo.delete_collection(collection)  # repo deletes+flushes
        await self.collection_repo.db.commit()


    async def search_user_collections(
        self,
        user_id: int,
        query: str,
        type_filter: str | None = None,
        skip: int | None = None,
        limit: int | None = None
    ) -> list[Collection]:
        """
        Service method to search collections for a user with validation.

        Args:
            user_id: The ID of the user.
            query: The search term (required).
            type_filter: Optional collection type filter (e.g., 'mixed', 'tasks-only').

        Returns:
            A list of Collection ORM objects matching the search criteria.

        Raises:
            HTTPException: If the query is too short.
        """
        # Basic validation
        if not query or len(query.strip()) < 2: # Require at least 2 non-whitespace chars
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long."
            )

        # Delegate to the repository
        collections = await self.collection_repo.search_collections(
            user_id=user_id,
            query=query.strip(), # Pass the stripped query
            type_filter=type_filter,
            skip=skip, 
            limit=limit
        )
        return list(collections)

def get_collection_service(
    collection_repo: CollectionRepository = Depends(get_collection_repository),
) -> CollectionService:
    return CollectionService(collection_repo)
