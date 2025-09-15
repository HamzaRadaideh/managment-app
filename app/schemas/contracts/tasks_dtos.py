# ======================
# TASKS SCHEMAS
# ======================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.enums.tasks_priorities import TaskPriority
from app.schemas.enums.tasks_status import TaskStatus
from app.schemas.contracts.tags_dtos import TagOut



class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    collection_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class TaskCreate(TaskBase):
    pass

class TaskOut(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    tag_ids: List[int] = []

    class Config:
        from_attributes = True
        
        
class TaskWithTags(TaskOut):
    tags: List[TagOut] = []

