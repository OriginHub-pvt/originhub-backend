"""
User database model (SQLAlchemy)
"""

from sqlalchemy import Column, String, Text
from app.database import Base


class User(Base):
    """
    User model for PostgreSQL database
    Synced with Clerk via webhooks

    Note: Clerk uses string IDs (not UUIDs), so user_id is stored as String
    """

    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True, index=True)  # Clerk uses string IDs
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(
        String(255), nullable=True
    )  # Usually not stored when using Clerk, but included per requirements
    bio = Column(Text, nullable=True)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"
