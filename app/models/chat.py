"""
Chat database models (SQLAlchemy)
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class Chat(Base):
    """
    Chat model for PostgreSQL database
    Represents a conversation between a user and the AI assistant
    """

    __tablename__ = "chats"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id = Column(
        String(255), ForeignKey("users.user_id"), nullable=False, index=True
    )
    title = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="chats")
    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Chat(id={self.id}, user_id={self.user_id}, title={self.title})>"


class Message(Base):
    """
    Message model for PostgreSQL database
    Represents individual messages within a chat
    """

    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    chat_id = Column(
        UUID(as_uuid=False),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Table-level constraint
    __table_args__ = (
        CheckConstraint("sender IN ('user', 'assistant')", name="check_sender"),
    )

    # Relationships
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, sender={self.sender})>"
