# app/api/services/notes_services.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from app.api.repositories.notes_repositories import (
    NoteRepository,
    get_note_repository,
)
from app.schemas.models.notes_models import Note
from app.schemas.models.collections_models import Collection # Import Collection model
from app.schemas.contracts.notes_dtos import NoteCreate, NoteBase
from app.schemas.enums.collections_types import CollectionType # Import the enum

class NoteService:
    def __init__(self, note_repo: NoteRepository):
        self.note_repo = note_repo

    async def get_user_notes(
        self, user_id: int, collection_id: int | None = None
    ) -> list[Note]:
        return await self.note_repo.get_notes_by_user(user_id=user_id, collection_id=collection_id)

    async def get_user_note_by_id(self, user_id: int, note_id: int) -> Note:
        note = await self.note_repo.get_note_by_id_and_user(note_id, user_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note

    async def create_note_for_user(self, user_id: int, note_create: NoteCreate) -> Note:
        data = note_create.dict()
        tag_ids = data.pop("tag_ids", None)
        data["user_id"] = user_id

        # Validate collection ownership AND type if provided
        if note_create.collection_id:
            owned_collection: Collection = await self.note_repo.get_collection_by_id_and_user(note_create.collection_id, user_id) # Annotate type
            if not owned_collection:
                raise HTTPException(
                    status_code=404, detail="Collection not found or not owned by user"
                )
            # --- NEW TYPE CHECK ---
            if owned_collection.type == CollectionType.TASKS_ONLY:
                 raise HTTPException(
                    status_code=400, detail=f"Cannot add a Note to a Collection of type '{CollectionType.TASKS_ONLY.value}'."
                )
            # --- END NEW TYPE CHECK ---

        # Validate tags if provided
        if tag_ids is not None:
            found = await self.note_repo.get_tags_by_ids_and_user(tag_ids, user_id)
            if len(found) != len(set(tag_ids)):
                found_ids = {t.id for t in found}
                missing = sorted(set(tag_ids) - found_ids)
                raise HTTPException(
                    status_code=400,
                    detail=f"Tags not found or not owned by user: {missing}",
                )

        new_note = await self.note_repo.create_note(data)
        if tag_ids is not None:
            await self.note_repo.set_note_tags(new_note, tag_ids)

        await self.note_repo.db.commit()
        await self.note_repo.db.refresh(new_note)                         # full
        await self.note_repo.db.refresh(new_note, attribute_names=["tags"])
        return new_note

    async def update_user_note(
        self, user_id: int, note_id: int, note_update: NoteBase
    ) -> Note:
        note = await self.get_user_note_by_id(user_id, note_id)

        update_data = note_update.dict(exclude_unset=True)
        tag_ids_to_set = update_data.pop("tag_ids", None)

        # Validate collection ownership AND type if changed/added
         # Check if collection_id is being set or changed (present in update_data)
        if "collection_id" in update_data:
            # This covers setting to a new ID or explicitly setting to None
            new_collection_id = update_data["collection_id"]
            if new_collection_id: # If it's being set to a non-null ID
                owned_collection: Collection = await self.note_repo.get_collection_by_id_and_user(
                    new_collection_id, user_id
                )
                if not owned_collection:
                    raise HTTPException(
                        status_code=404, detail="Collection not found or not owned by user"
                    )
                # --- NEW TYPE CHECK ---
                if owned_collection.type == CollectionType.TASKS_ONLY:
                    raise HTTPException(
                        status_code=400, detail=f"Cannot add a Note to a Collection of type '{CollectionType.TASKS_ONLY.value}'."
                    )
                # --- END NEW TYPE CHECK ---
            # If new_collection_id is None, it's fine (removing from collection), so no check needed.

        # Validate tags if provided
        if tag_ids_to_set is not None:
            found = await self.note_repo.get_tags_by_ids_and_user(tag_ids_to_set, user_id)
            if len(found) != len(set(tag_ids_to_set)):
                found_ids = {t.id for t in found}
                missing = sorted(set(tag_ids_to_set) - found_ids)
                raise HTTPException(
                    status_code=400,
                    detail=f"Tags not found or not owned by user: {missing}",
                )

        # Apply changes
        if update_data:
            await self.note_repo.update_note(note, update_data)
        if tag_ids_to_set is not None:
            await self.note_repo.set_note_tags(note, tag_ids_to_set)

        await self.note_repo.db.commit()
        await self.note_repo.db.refresh(note)                              # full
        await self.note_repo.db.refresh(note, attribute_names=["tags"])    # tags
        return note

    async def delete_user_note(self, user_id: int, note_id: int) -> None:
        # Ensure the note exists and belongs to the user
        note = await self.get_user_note_by_id(user_id, note_id)
        # Delete via repository (repo currently deletes+flushes)
        await self.note_repo.delete_note(note)
        # Persist deletion
        await self.note_repo.db.commit()

    async def search_user_notes(
        self,
        user_id: int,
        query: str,
        collection_id: Optional[int] = None,
        skip: int | None = None,
        limit: int | None = None
    ) -> list[Note]:
        """
        Service method to search notes for a user with validation.

        Args:
            user_id: The ID of the user.
            query: The search term (required).
            collection_id: Optional collection ID filter.

        Returns:
            A list of Note ORM objects matching the search criteria.

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
        notes = await self.note_repo.search_notes(
            user_id=user_id,
            query=query.strip(), # Pass the stripped query
            collection_id=collection_id,
            skip=skip, 
            limit=limit
        )
        return list(notes)

def get_note_service(note_repo: NoteRepository = Depends(get_note_repository)) -> NoteService:
    return NoteService(note_repo)
