# ======================
# TAGS SCHEMAS
# ======================

from pydantic import BaseModel, Field
from datetime import datetime


class TagBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)

class TagCreate(TagBase):
    pass

class TagOut(TagBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

