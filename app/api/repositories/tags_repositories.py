# app/api/repositories/tags_repositories.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Sequence
from app.schemas.database import get_async_session
from app.schemas.models.tags_models import Tag

class TagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tags_by_user(self, user_id: int) -> Sequence[Tag]:
        stmt = select(Tag).where(Tag.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_tag_by_id(self, tag_id: int) -> Tag | None:
        return await self.db.get(Tag, tag_id)

    async def get_tag_by_id_and_user(self, tag_id: int, user_id: int) -> Tag | None:
        result = await self.db.execute(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_tag_by_title_and_user(self, title: str, user_id: int) -> Tag | None:
        result = await self.db.execute(
            select(Tag).where(Tag.title == title, Tag.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_tag(self, tag_data: dict) -> Tag:
        db_tag = Tag(**tag_data)
        self.db.add(db_tag)
        await self.db.flush()
        await self.db.refresh(db_tag)
        return db_tag

    async def update_tag(self, tag: Tag, title: str):
        tag.title = title
        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def delete_tag(self, tag: Tag):
        await self.db.delete(tag)
        await self.db.flush()


    async def search_tags(
        self,
        user_id: int,
        query: str,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Tag]:
        """
        Search for tags belonging to a user by title (case-insensitive, infix).

        Args:
            user_id: The ID of the user whose tags to search.
            query: The search term for title (case-insensitive, infix).

        Returns:
            A sequence of Tag objects matching the criteria.
        """
        stmt = select(Tag).where(Tag.user_id == user_id)

        # Apply text search (case-insensitive infix match on title)
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(Tag.title.ilike(search_term))

        # Order results (e.g., by last updated, descending, or alphabetically)
        stmt = stmt.order_by(Tag.updated_at.desc()) # Or Tag.title.asc()
        if skip is not None:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
            
        result = await self.db.execute(stmt)
        return result.scalars().all()

# Dependency
def get_tag_repository(
    db: AsyncSession = Depends(get_async_session)
) -> TagRepository:
    return TagRepository(db)

