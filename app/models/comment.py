"""
Comment database model (SQLAlchemy)
Tracks comments on ideas
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class Comment(Base):
    """
    Comment model for tracking user comments on ideas.
    """

    __tablename__ = "comments"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    idea_id = Column(
        UUID(as_uuid=False),
        ForeignKey("ideas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(255),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    parent_comment_id = Column(
        UUID(as_uuid=False),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    idea = relationship("Idea", backref="comments")
    user = relationship("User", backref="comments")
    parent_comment = relationship(
        "Comment", remote_side=[id], backref="replies", foreign_keys=[parent_comment_id]
    )

    def __repr__(self):
        return (
            f"<Comment(id={self.id}, idea_id={self.idea_id}, user_id={self.user_id})>"
        )
