"""
Authentication and authorization dependencies
"""

from fastapi import Header, HTTPException
from typing import Optional


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> str:
    """
    Extract the current user's Clerk user ID from the X-User-Id header.

    The frontend should send the Clerk user ID in the X-User-Id header.
    This is a simple approach - in production, you might want to verify
    JWT tokens from Clerk instead.

    Args:
        x_user_id: User ID from X-User-Id header

    Returns:
        The user ID as a string

    Raises:
        HTTPException: 401 if user ID is not provided
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide X-User-Id header.",
        )
    return x_user_id
