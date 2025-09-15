# app/schemas/models/tags_models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.schemas.database import Base

# ================================================
# IMPORTANT: Define association tables FIRST!
# ================================================

# Association table: Tags <-> Tasks
tag_task_association = Table(
    "tag_task_association",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
)

# Association table: Tags <-> Notes
tag_note_association = Table(
    "tag_note_association",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
)

# Association table: Tags <-> Collections
tag_collection_association = Table(
    "tag_collection_association",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("collections.id"), primary_key=True),
)

# ================================================
# Now define the Tag model (which USES them)
# ================================================

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships (using string names for models and association tables)
    user = relationship("User", back_populates="tags")
    tasks = relationship("Task", secondary="tag_task_association", back_populates="tags") # String for secondary
    notes = relationship("Note", secondary="tag_note_association", back_populates="tags") # String for secondary
    collections = relationship("Collection", secondary="tag_collection_association", back_populates="tags") # String for secondary

    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='unique_user_tag_title'),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, title='{self.title}')>"

