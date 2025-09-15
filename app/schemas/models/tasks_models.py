# app/schemas/models/tasks_models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.schemas.enums.tasks_priorities import TaskPriority
from app.schemas.enums.tasks_status import TaskStatus
from app.schemas.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships (using string names for models and association tables)
    user = relationship("User", back_populates="tasks")
    collection = relationship("Collection", back_populates="tasks")
    tags = relationship("Tag", secondary="tag_task_association",
                        back_populates="tasks", lazy="selectin")

    @property
    def tag_ids(self) -> list[int]:
        return [t.id for t in (self.tags or [])]

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

