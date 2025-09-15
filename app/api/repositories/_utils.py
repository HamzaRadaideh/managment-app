# app/api/repositories/_utils.py
from typing import Iterable, List
from fastapi import HTTPException
from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.models.tags_models import Tag


async def _load_tags(
    session: AsyncSession,
    user_id: int,
    tag_ids: Iterable[int],
    require_all: bool = True,
) -> List[Tag]:
    """Load Tag rows for a user by IDs. Optionally enforce that all IDs exist."""
    ids = list(dict.fromkeys(tag_ids))  # dedupe, preserve order
    if not ids:
        return []
    res = await session.execute(
        select(Tag).where(Tag.user_id == user_id, Tag.id.in_(ids))
    )
    tags = list(res.scalars().all())

    if require_all and len(tags) != len(set(ids)):
        found = {t.id for t in tags}
        missing = sorted(set(ids) - found)
        raise HTTPException(
            status_code=400,
            detail=f"Tags not found or not owned by user: {missing}",
        )
    return tags


def _is_new_or_pending(obj) -> bool:
    st = inspect(obj)
    return st.transient or st.pending

