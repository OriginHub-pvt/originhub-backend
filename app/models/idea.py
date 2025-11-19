"""
Idea database model (SQLAlchemy)
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class Idea(Base):
    """
    Idea model for PostgreSQL database
    Migrated from Weaviate with same schema plus user_id field
    """

    __tablename__ = "ideas"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    marketSize = Column(String(255), nullable=False)
    tags = Column(ARRAY(String), nullable=True, default=list)
    author = Column(String(255), nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    upvotes = Column(Integer, nullable=False, default=0)
    views = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="draft")
    user_id = Column(
        String(255), ForeignKey("users.user_id"), nullable=True, index=True
    )
    link = Column(Text, nullable=True)

    # Relationship to User
    user = relationship("User", backref="ideas")

    def __repr__(self):
        return f"<Idea(id={self.id}, title={self.title}, user_id={self.user_id})>"
