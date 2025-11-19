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
    link: Optional[str] = Field(None, description="Link to the idea")


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
    link: Optional[str] = None


class IdeaListResponse(BaseModel):
    success: bool = True
    data: dict
    message: Optional[str] = None


class IdeaUpdate(BaseModel):
    """Schema for partial idea updates"""

    title: Optional[str] = Field(None, description="Idea title")
    description: Optional[str] = Field(None, description="Idea description")
    problem: Optional[str] = Field(None, description="Problem statement")
    solution: Optional[str] = Field(None, description="Proposed solution")
    marketSize: Optional[str] = Field(None, description="Market size")
    tags: Optional[List[str]] = Field(None, description="Tags for the idea")
    link: Optional[str] = Field(None, description="Link to the idea")


class IdeaCreateResponse(BaseModel):
    success: bool = True
    data: dict
    message: str = "Idea created successfully"


class IdeaDetailResponse(BaseModel):
    """Response for single idea retrieval"""

    success: bool = True
    data: IdeaResponse
    message: Optional[str] = None


class IdeaDeleteResponse(BaseModel):
    """Response for idea deletion"""

    success: bool = True
    message: str = "Idea deleted successfully"
