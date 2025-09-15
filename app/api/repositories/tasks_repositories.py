from typing import Iterable, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.repositories._utils import _is_new_or_pending, _load_tags
from app.schemas.database import get_async_session
from app.schemas.models.collections_models import Collection
from app.schemas.models.tags_models import Tag
from app.schemas.models.tasks_models import Task


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tasks_by_user(
        self,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        collection_id: Optional[int] = None,
    ) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .options(selectinload(Task.tags))
        )
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if collection_id:
            stmt = stmt.where(Task.collection_id == collection_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_task_by_id(self, task_id: int) -> Task | None:
        return await self.db.get(Task, task_id)

    async def get_task_by_id_and_user(self, task_id: int, user_id: int) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(selectinload(Task.tags))
        )
        return result.scalar_one_or_none()

    async def create_task(self, task_data: dict) -> Task:
        db_task = Task(**task_data)
        self.db.add(db_task)
        await self.db.flush()  # service will commit
        return db_task

    async def update_task(self, task: Task, update_data: dict) -> Task:
        for key, value in update_data.items():
            setattr(task, key, value)
        await self.db.flush()
        return task

    async def delete_task(self, task: Task) -> None:
        await self.db.delete(task)
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

    async def set_task_tags(self, task: Task, tag_ids: Iterable[int]) -> None:
        """Replace task.tags with given tag IDs (async-safe)."""
        tags = await _load_tags(self.db, user_id=task.user_id, tag_ids=tag_ids)

        if _is_new_or_pending(task):
            task.tags = tags
        else:
            await self.db.refresh(task, attribute_names=["tags"])
            task.tags.clear()
            task.tags.extend(tags)

        await self.db.flush()


    async def search_tasks(
        self,
        user_id: int,
        query: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        collection_id: Optional[int] = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Task]:
        """
        Search for tasks belonging to a user, with optional filters and text search.

        Args:
            user_id: The ID of the user whose tasks to search.
            query: The search term for title/description (case-insensitive, infix).
            status: Optional filter for task status.
            priority: Optional filter for task priority.
            collection_id: Optional filter for collection ID.

        Returns:
            A sequence of Task objects matching the criteria.
        """
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .options(selectinload(Task.tags)) # Ensure tags are loaded
        )

        # Apply filters
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if collection_id:
            stmt = stmt.where(Task.collection_id == collection_id)

        # Apply text search (case-insensitive infix match)
        if query:
            # Basic escaping for LIKE wildcards (optional, for stricter matching)
            # escaped_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            # search_term = f"%{escaped_query}%"
            # stmt = stmt.where(
            #     (Task.title.ilike(search_term)) |
            #     (Task.description.ilike(search_term))
            # ).params(escape_char='\\') # Requires setting ESCAPE in raw SQL or using func

            # Simpler approach using standard parameter binding (SQLAlchemy handles % correctly)
            # This allows user input like "10%" to match literally if present.
            search_term = f"%{query}%"
            stmt = stmt.where(
                (Task.title.ilike(search_term)) |
                (Task.description.ilike(search_term))
            )

        # Order results (e.g., by last updated, descending)
        stmt = stmt.order_by(Task.updated_at.desc())
        if skip is not None:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()


def get_task_repository(db: AsyncSession = Depends(get_async_session)) -> TaskRepository:
    return TaskRepository(db)

