from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any
from app.models import IdeaCreate, IdeaListResponse, IdeaCreateResponse
from app.services.ideas_service import ideas_service

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
    Get all ideas from the database (Weaviate) and send to frontend.
    Returns all data including: id, title, description, problem, solution,
    marketSize, tags, author, createdAt, upvotes, views, and status.
    
    Supports optional filtering by search query and tags, and sorting.
    """
    try:
        # Get all ideas from Weaviate database
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
    Create a new idea and store it in Weaviate.
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
    This endpoint accepts a flexible JSON structure and stores it in Weaviate.
    
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
    """
    try:
        # Validate required fields
        required_fields = ["title", "description", "problem", "solution", "marketSize", "author"]
        missing_fields = [field for field in required_fields if field not in idea_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Add idea using the add_idea method
        new_idea = ideas_service.add_idea(idea_data)

        return IdeaCreateResponse(
            success=True,
            data={"id": new_idea["id"]},
            message="Idea added successfully to Weaviate",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
