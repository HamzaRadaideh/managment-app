# ======================
# USERS SCHEMAS
# ======================

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from app.schemas.contracts.tags_dtos import TagOut
from app.schemas.contracts.collections_dtos import CollectionOut
from app.schemas.contracts.tasks_dtos import TaskOut
from app.schemas.contracts.notes_dtos import NoteOut


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    fname: str = Field(..., min_length=1, max_length=50)
    lname: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy ORM compatibility


class UserWithDetails(UserOut):
    collections: List[CollectionOut] = []
    tasks: List[TaskOut] = []
    notes: List[NoteOut] = []
    tags: List[TagOut] = []
    

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

