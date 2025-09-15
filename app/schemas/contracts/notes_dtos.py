# ======================
# NOTES SCHEMAS
# ======================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.contracts.tags_dtos import TagOut


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    collection_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class NoteCreate(NoteBase):
    pass

class NoteOut(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    tag_ids: List[int] = []

    class Config:
        from_attributes = True

class NoteWithTags(NoteOut):
    tags: List[TagOut] = []

