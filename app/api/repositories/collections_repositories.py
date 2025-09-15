from typing import Iterable, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.repositories._utils import _is_new_or_pending, _load_tags
from app.schemas.database import get_async_session
from app.schemas.models.collections_models import Collection
from app.schemas.models.tags_models import Tag


class CollectionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_collections_by_user(
        self, user_id: int, type_filter: Optional[str] = None
    ) -> Sequence[Collection]:
        stmt = (
            select(Collection)
            .where(Collection.user_id == user_id)
            .options(selectinload(Collection.tags))
        )
        if type_filter:
            stmt = stmt.where(Collection.type == type_filter)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_collection_by_id(self, collection_id: int) -> Collection | None:
        return await self.db.get(Collection, collection_id)

    async def get_collection_by_id_and_user(
        self, collection_id: int, user_id: int
    ) -> Collection | None:
        result = await self.db.execute(
            select(Collection)
            .where(Collection.id == collection_id, Collection.user_id == user_id)
            .options(selectinload(Collection.tags))
        )
        return result.scalar_one_or_none()

    async def get_collection_by_title_and_user(
        self, title: str, user_id: int
    ) -> Collection | None:
        result = await self.db.execute(
            select(Collection).where(Collection.title == title, Collection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_collection(self, collection_data: dict) -> Collection:
        db_collection = Collection(**collection_data)
        self.db.add(db_collection)
        await self.db.flush()
        return db_collection

    async def update_collection(self, collection: Collection, update_data: dict) -> Collection:
        for key, value in update_data.items():
            setattr(collection, key, value)
        await self.db.flush()
        return collection

    async def delete_collection(self, collection: Collection) -> None:
        await self.db.delete(collection)
        await self.db.flush()

    async def preload_collection_items(self, collection: Collection) -> None:
        # Only if you need tasks/notes in the same response
        await self.db.refresh(collection, attribute_names=["tasks", "notes"])

    async def get_tags_by_ids_and_user(
        self, tag_ids: list[int], user_id: int
    ) -> Sequence[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
        )
        return result.scalars().all()

    async def set_collection_tags(self, collection: Collection, tag_ids: Iterable[int]) -> None:
        """Replace collection.tags with given tag IDs (async-safe)."""
        tags = await _load_tags(self.db, collection.user_id, tag_ids)

        if _is_new_or_pending(collection):
            collection.tags = tags
        else:
            await self.db.refresh(collection, attribute_names=["tags"])
            collection.tags.clear()
            collection.tags.extend(tags)

        await self.db.flush()

    async def search_collections(
        self,
        user_id: int,
        query: str,
        type_filter: Optional[str] = None,
        skip: int | None = None,
        limit: int | None = None
    ) -> Sequence[Collection]:
        """
        Search for collections belonging to a user, with an optional type filter and text search.

        Args:
            user_id: The ID of the user whose collections to search.
            query: The search term for title/description (case-insensitive, infix).
            type_filter: Optional filter for collection type (e.g., 'mixed', 'tasks-only').

        Returns:
            A sequence of Collection objects matching the criteria.
        """
        stmt = (
            select(Collection)
            .where(Collection.user_id == user_id)
            .options(selectinload(Collection.tags)) # Ensure tags are loaded
        )

        # Apply type filter
        if type_filter is not None:
            stmt = stmt.where(Collection.type == type_filter)

        # Apply text search (case-insensitive infix match on title)
        # Optionally include description: (Collection.title.ilike(...) | Collection.description.ilike(...))
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(Collection.title.ilike(search_term))
            # If you want to search description too:
            # stmt = stmt.where(
            #     (Collection.title.ilike(search_term)) |
            #     (Collection.description.ilike(search_term))
            # )

        # Order results (e.g., by last updated, descending)
        stmt = stmt.order_by(Collection.updated_at.desc())
        if skip is not None:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

def get_collection_repository(db: AsyncSession = Depends(get_async_session)) -> CollectionRepository:
    return CollectionRepository(db)

