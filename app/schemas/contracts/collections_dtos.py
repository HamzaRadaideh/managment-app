# ======================
# COLLECTIONS SCHEMAS
# ======================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.enums.collections_types import CollectionType
from app.schemas.contracts.tasks_dtos import TaskOut
from app.schemas.contracts.notes_dtos import NoteOut



class CollectionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: CollectionType = CollectionType.MIXED
    tag_ids: Optional[List[int]] = None

class CollectionCreate(CollectionBase):
    pass

class CollectionOut(CollectionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0
    note_count: Optional[int] = 0

    class Config:
        from_attributes = True


class CollectionWithItems(CollectionOut):
    tasks: List[TaskOut] = []
    notes: List[NoteOut] = []
    tag_ids: List[int] = []

