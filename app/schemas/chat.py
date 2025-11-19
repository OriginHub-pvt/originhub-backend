"""
Chat request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    success: bool = True
    data: dict
    message: Optional[str] = None
