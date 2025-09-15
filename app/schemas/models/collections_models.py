# app/schemas/models/collections_models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.schemas.enums.collections_types import CollectionType
from app.schemas.database import Base

class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(CollectionType), nullable=False, default=CollectionType.MIXED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships (using string names for models and association tables)
    user = relationship("User", back_populates="collections")
    tasks = relationship("Task", back_populates="collection", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="collection", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="tag_collection_association",
                        back_populates="collections", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='unique_user_collection_title'),
    )
    
    @property
    def tag_ids(self) -> list[int]:
        return [t.id for t in (self.tags or [])]

    def __repr__(self):
        return f"<Collection(id={self.id}, title='{self.title}', type='{self.type}')>"

