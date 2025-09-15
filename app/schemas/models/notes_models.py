# app/schemas/models/notes_models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.schemas.database import Base

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships (using string names for models and association tables)
    user = relationship("User", back_populates="notes")
    collection = relationship("Collection", back_populates="notes")
    tags = relationship("Tag", secondary="tag_note_association",
                        back_populates="notes", lazy="selectin")

    @property
    def tag_ids(self) -> list[int]:
        return [t.id for t in (self.tags or [])]

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"

