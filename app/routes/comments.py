"""
Comment API routes
"""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas import (
    CommentCreate,
    CommentResponse,
    CommentListResponse,
    CommentCreateResponse,
    CommentDeleteResponse,
)
from app.services.comments_service import comments_service
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/ideas/{idea_id}/comments", tags=["comments"])


@router.post("", response_model=CommentCreateResponse, status_code=201)
async def create_comment(
    idea_id: str,
    comment_data: CommentCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a comment on an idea or a reply to another comment.
    To create a reply, include parent_comment_id in the request body.
    Any authenticated user can comment on any idea or reply to any comment.

    Requires authentication via X-User-Id header.
    """
    try:
        comment = comments_service.create_comment(idea_id, comment_data, user_id)

        if not comment:
            raise HTTPException(
                status_code=404, detail=f"Idea with id {idea_id} not found"
            )

        return CommentCreateResponse(
            success=True,
            data=CommentResponse(**comment),
            message="Comment created successfully",
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("", response_model=CommentListResponse)
async def get_idea_comments(idea_id: str):
    """
    Get all comments for an idea, organized as a tree structure with nested replies.
    Returns top-level comments ordered by creation date (newest first),
    with replies nested under their parent comments.

    No authentication required - comments are public.
    """
    try:
        comments = comments_service.get_idea_comments(idea_id)

        return CommentListResponse(
            success=True,
            data=[CommentResponse(**comment) for comment in comments],
            total=len(comments),
            message=f"Found {len(comments)} comments",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{comment_id}", response_model=CommentDeleteResponse, status_code=200)
async def delete_comment(
    idea_id: str,
    comment_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete a comment.
    Only the comment author OR the idea owner can delete a comment.

    Requires authentication via X-User-Id header.
    Returns 403 Forbidden if user doesn't have permission.
    Returns 404 Not Found if comment doesn't exist.
    """
    try:
        deleted = comments_service.delete_comment(comment_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Comment with id {comment_id} not found"
            )

        return CommentDeleteResponse(
            success=True, message="Comment deleted successfully"
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif (
            "permission" in error_msg.lower()
            or "don't have permission" in error_msg.lower()
        ):
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

