from typing import Iterable, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.repositories._utils import _is_new_or_pending, _load_tags
from app.schemas.database import get_async_session
from app.schemas.models.collections_models import Collection
from app.schemas.models.notes_models import Note
from app.schemas.models.tags_models import Tag


class NoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_notes_by_user(
        self, user_id: int, collection_id: Optional[int] = None
    ) -> Sequence[Note]:
        stmt = (
            select(Note)
            .where(Note.user_id == user_id)
            .options(selectinload(Note.tags))
        )
        if collection_id:
            stmt = stmt.where(Note.collection_id == collection_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_note_by_id(self, note_id: int) -> Note | None:
        return await self.db.get(Note, note_id)

    async def get_note_by_id_and_user(self, note_id: int, user_id: int) -> Note | None:
        result = await self.db.execute(
            select(Note)
            .where(Note.id == note_id, Note.user_id == user_id)
            .options(selectinload(Note.tags))
        )
        return result.scalar_one_or_none()

    async def create_note(self, note_data: dict) -> Note:
        db_note = Note(**note_data)
        self.db.add(db_note)
        await self.db.flush()
        return db_note

    async def update_note(self, note: Note, update_data: dict) -> Note:
        for key, value in update_data.items():
            setattr(note, key, value)
        await self.db.flush()
        return note

    async def delete_note(self, note: Note) -> None:
        await self.db.delete(note)
        await self.db.flush()

    async def get_collection_by_id_and_user(
        self, collection_id: int, user_id: int
    ) -> Collection | None:
        result = await self.db.execute(
            select(Collection).where(
                Collection.id == collection_id,
                Collection.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_tags_by_ids_and_user(
        self, tag_ids: list[int], user_id: int
    ) -> Sequence[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
        )
        return result.scalars().all()

    async def set_note_tags(self, note: Note, tag_ids: Iterable[int]) -> None:
        """Replace note.tags with given tag IDs (async-safe)."""
        tags = await _load_tags(self.db, user_id=note.user_id, tag_ids=tag_ids)

        if _is_new_or_pending(note):
            note.tags = tags
        else:
            await self.db.refresh(note, attribute_names=["tags"])
            note.tags.clear()
            note.tags.extend(tags)

        await self.db.flush()


    async def search_notes(
        self,
        user_id: int,
        query: str,
        collection_id: Optional[int] = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Note]:
        """
        Search for notes belonging to a user, with an optional collection filter and text search.

        Args:
            user_id: The ID of the user whose notes to search.
            query: The search term for title/description (case-insensitive, infix).
            collection_id: Optional filter for collection ID.

        Returns:
            A sequence of Note objects matching the criteria.
        """
        stmt = (
            select(Note)
            .where(Note.user_id == user_id)
            .options(selectinload(Note.tags)) # Ensure tags are loaded
        )

        # Apply collection filter
        if collection_id is not None: # Explicitly check for None
            stmt = stmt.where(Note.collection_id == collection_id)

        # Apply text search (case-insensitive infix match)
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                (Note.title.ilike(search_term)) |
                (Note.description.ilike(search_term))
            )

        # Order results (e.g., by last updated, descending)
        stmt = stmt.order_by(Note.updated_at.desc())
        if skip is not None:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()


def get_note_repository(db: AsyncSession = Depends(get_async_session)) -> NoteRepository:
    return NoteRepository(db)

