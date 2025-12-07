"""
Comment Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommentBase(BaseModel):
    """Base comment schema"""

    content: str = Field(
        ..., min_length=1, max_length=5000, description="Comment content"
    )


class CommentCreate(CommentBase):
    """Schema for creating a comment"""

    parent_comment_id: Optional[str] = Field(
        None, description="ID of parent comment if this is a reply"
    )


class CommentResponse(CommentBase):
    """Schema for comment response with nested replies"""

    id: str
    idea_id: str
    user_id: str
    parent_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    replies: List["CommentResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Schema for list of comments response"""

    success: bool
    data: list[CommentResponse]
    total: int
    message: str


class CommentCreateResponse(BaseModel):
    """Schema for comment creation response"""

    success: bool
    data: CommentResponse
    message: str


class CommentDeleteResponse(BaseModel):
    """Schema for comment deletion response"""

    success: bool
    message: str


# Update forward references for nested CommentResponse
CommentResponse.model_rebuild()
