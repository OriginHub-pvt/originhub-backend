"""
Idea Upvote junction table model (SQLAlchemy)
Tracks which users have upvoted which ideas
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class IdeaUpvote(Base):
    """
    Junction table to track user upvotes on ideas.
    Many-to-many relationship: User <-> Idea
    """

    __tablename__ = "idea_upvotes"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id = Column(
        String(255),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idea_id = Column(
        UUID(as_uuid=False),
        ForeignKey("ideas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Unique constraint: a user can only upvote an idea once
    __table_args__ = (
        UniqueConstraint("user_id", "idea_id", name="unique_user_idea_upvote"),
    )

    # Relationships
    user = relationship("User", backref="idea_upvotes")
    idea = relationship("Idea", backref="upvote_records")

    def __repr__(self):
        return f"<IdeaUpvote(user_id={self.user_id}, idea_id={self.idea_id})>"
