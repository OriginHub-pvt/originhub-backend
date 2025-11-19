"""
Pydantic schemas for request/response validation
"""

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatBase,
    ChatCreate,
    ChatListResponse,
    MessageBase,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ChatSendResponse,
    ChatSummaryResponse,
    ChatDeleteResponse,
)
from app.schemas.idea import (
    IdeaCreate,
    IdeaResponse,
    IdeaListResponse,
    IdeaCreateResponse,
    IdeaUpdate,
    IdeaDetailResponse,
    IdeaDeleteResponse,
)
from app.schemas.user import UserBase, UserResponse, UserCreate, UserUpdate

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "ChatBase",
    "ChatCreate",
    "ChatListResponse",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "MessageListResponse",
    "ChatSendResponse",
    "ChatSummaryResponse",
    "ChatDeleteResponse",
    # Idea schemas
    "IdeaCreate",
    "IdeaResponse",
    "IdeaListResponse",
    "IdeaCreateResponse",
    "IdeaUpdate",
    "IdeaDetailResponse",
    "IdeaDeleteResponse",
    # User schemas
    "UserBase",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
]
