"""
Chat request/response schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ChatBase(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    last_message_at: datetime


class ChatCreate(BaseModel):
    """Schema for creating a new chat"""

    user_id: str = Field(..., description="Clerk user ID")


class ChatResponse(BaseModel):
    """Response schema for a single chat"""

    id: str
    user_id: str
    title: Optional[str] = None
    created_at: str
    last_message_at: str

    model_config = ConfigDict(from_attributes=True)


class ChatListResponse(BaseModel):
    """Response schema for list of chats"""

    success: bool = True
    data: dict
    message: Optional[str] = None


class MessageBase(BaseModel):
    id: str
    chat_id: str
    sender: str
    message: str
    created_at: datetime


class MessageCreate(BaseModel):
    """Schema for creating a new message"""

    message: str = Field(..., description="Message content")
    chat_id: Optional[str] = Field(
        None, description="Chat ID (optional, creates new chat if not provided)"
    )
    stream: bool = Field(
        False, description="Whether to stream the response token-by-token"
    )


class MessageResponse(BaseModel):
    """Response schema for a single message"""

    id: str
    chat_id: str
    sender: str
    message: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    """Response schema for list of messages"""

    success: bool = True
    data: dict
    message: Optional[str] = None


# Legacy schemas for backward compatibility
class ChatRequest(BaseModel):
    """Legacy schema - use MessageCreate instead"""

    message: str = Field(..., description="User message")


class ChatSendResponse(BaseModel):
    """Response schema for sending a message"""

    success: bool = True
    data: dict
    message: Optional[str] = None


class ChatSummaryResponse(BaseModel):
    """Response schema for chat summary"""

    success: bool = True
    data: dict
    message: Optional[str] = None


class ChatDeleteResponse(BaseModel):
    """Response schema for chat deletion"""

    success: bool = True
    message: str = "Chat deleted successfully"


class ConvertToIdeaRequest(BaseModel):
    """Schema for converting chat to idea"""

    chat_id: str = Field(..., description="Chat ID to convert to idea")
