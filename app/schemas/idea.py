"""
Idea request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class IdeaCreate(BaseModel):
    title: str = Field(..., description="Idea title")
    description: str = Field(..., description="Idea description")
    problem: str = Field(..., description="Problem statement")
    solution: str = Field(..., description="Proposed solution")
    marketSize: str = Field(..., description="Market size")
    tags: List[str] = Field(default_factory=list, description="Tags for the idea")
    author: str = Field(..., description="Author name")


class IdeaResponse(BaseModel):
    id: str
    title: str
    description: str
    problem: str
    solution: str
    marketSize: str
    tags: List[str]
    author: str
    createdAt: str
    upvotes: int
    views: int
    status: str
    user_id: Optional[str] = None


class IdeaListResponse(BaseModel):
    success: bool = True
    data: dict
    message: Optional[str] = None


class IdeaCreateResponse(BaseModel):
    success: bool = True
    data: dict
    message: str = "Idea created successfully"
