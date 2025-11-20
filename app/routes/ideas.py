from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import Optional, Dict, Any
from app.schemas import (
    IdeaCreate,
    IdeaListResponse,
    IdeaCreateResponse,
    IdeaUpdate,
    IdeaDetailResponse,
    IdeaResponse,
    IdeaDeleteResponse,
)
from app.services.ideas_service import ideas_service
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=IdeaListResponse)
async def get_ideas(
    search: Optional[str] = Query(None, description="Search query for filtering ideas"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    sort_by: Optional[str] = Query(
        "createdAt", description="Sort field (createdAt, title)"
    ),
):
    """
    Get all ideas from the database (PostgreSQL) and send to frontend.
    Returns all data including: id, title, description, problem, solution,
    marketSize, tags, author, createdAt, upvotes, views, status, and user_id.

    Supports optional filtering by search query and tags, and sorting.
    """
    try:
        # Get all ideas from PostgreSQL database
        all_ideas = ideas_service.get_all_ideas(
            search=search, tags=tags, sort_by=sort_by
        )

        return IdeaListResponse(
            success=True,
            data={"ideas": all_ideas},
            message=f"Retrieved {len(all_ideas)} ideas from database",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=IdeaCreateResponse, status_code=201)
async def create_idea(idea: IdeaCreate):
    """
    Create a new idea and store it in PostgreSQL.
    """
    try:
        new_idea = ideas_service.create_idea(idea)

        return IdeaCreateResponse(
            success=True,
            data={"id": new_idea["id"]},
            message="Idea created successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/add", response_model=IdeaCreateResponse, status_code=201)
async def add_idea(idea_data: Dict[str, Any] = Body(...)):
    """
    Add an idea directly using a dictionary.
    This endpoint accepts a flexible JSON structure and stores it in PostgreSQL.

    Request body should contain:
    - title (required)
    - description (required)
    - problem (required)
    - solution (required)
    - marketSize (required)
    - tags (optional, list of strings)
    - author (required)
    - id (optional, will be generated if not provided)
    - upvotes (optional, defaults to 0)
    - views (optional, defaults to 0)
    - status (optional, defaults to "draft")
    - user_id (optional, user ID to associate with the idea)
    - link (optional, link to the idea)
    """
    try:
        # Validate required fields
        required_fields = [
            "title",
            "description",
            "problem",
            "solution",
            "marketSize",
            "author",
        ]
        missing_fields = [field for field in required_fields if field not in idea_data]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        # Add idea using the add_idea method
        new_idea = ideas_service.add_idea(idea_data)

        return IdeaCreateResponse(
            success=True,
            data={"id": new_idea["id"]},
            message="Idea added successfully to PostgreSQL",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
async def get_idea_by_id(idea_id: str):
    """
    Get a single idea by ID from the database.
    Returns all idea data including user_id for ownership checking.
    """
    try:
        idea = ideas_service.get_idea_by_id(idea_id)

        if not idea:
            raise HTTPException(
                status_code=404, detail=f"Idea with id {idea_id} not found"
            )

        return IdeaDetailResponse(
            success=True,
            data=IdeaResponse(**idea),
            message="Idea retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{idea_id}/view", response_model=IdeaDetailResponse)
async def increment_idea_views(idea_id: str):
    """
    Increment the view count for an idea by 1.
    Each time this endpoint is called, the idea's view count increases by 1.
    
    No authentication required - anyone can view ideas.
    """
    try:
        updated_idea = ideas_service.increment_views(idea_id)

        if not updated_idea:
            raise HTTPException(
                status_code=404, detail=f"Idea with id {idea_id} not found"
            )

        return IdeaDetailResponse(
            success=True,
            data=IdeaResponse(**updated_idea),
            message="View count incremented successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{idea_id}", response_model=IdeaDetailResponse)
async def update_idea(
    idea_id: str, idea_update: IdeaUpdate, user_id: str = Depends(get_current_user_id)
):
    """
    Update an idea. Only the owner can update their idea.

    Requires authentication via X-User-Id header.
    Returns 403 Forbidden if the user is not the owner.

    Supports partial updates - only include fields you want to update.
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = idea_update.model_dump(exclude_unset=True)

        # If no fields to update, return error
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Update the idea (service will check ownership)
        updated_idea = ideas_service.update_idea(
            idea_id=idea_id, update_data=update_data, user_id=user_id
        )

        return IdeaDetailResponse(
            success=True,
            data=IdeaResponse(**updated_idea),
            message="Idea updated successfully",
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif (
            "permission" in error_msg.lower()
            or "not have permission" in error_msg.lower()
        ):
            raise HTTPException(status_code=403, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{idea_id}", response_model=IdeaDeleteResponse, status_code=200)
async def delete_idea(idea_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Delete an idea. Only the owner can delete their idea.

    Requires authentication via X-User-Id header.
    Returns 403 Forbidden if the user is not the owner.
    Returns 404 Not Found if the idea doesn't exist.
    """
    try:
        # Delete the idea (service will check ownership)
        ideas_service.delete_idea(idea_id=idea_id, user_id=user_id)

        return IdeaDeleteResponse(success=True, message="Idea deleted successfully")

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif (
            "permission" in error_msg.lower()
            or "not have permission" in error_msg.lower()
        ):
            raise HTTPException(status_code=403, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
