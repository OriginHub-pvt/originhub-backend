from typing import List, Dict, Optional
from app.schemas import IdeaCreate
import uuid
from datetime import datetime
from app.services.weaviate_service import weaviate_service


class IdeasService:
    """
    Service layer for ideas data operations.
    This abstracts data access logic and can be easily replaced with database calls later.
    """

    @staticmethod
    def _convert_weaviate_to_idea_format(weaviate_result: Dict) -> Dict:
        """
        Convert Weaviate result format to our standard idea format.

        Args:
            weaviate_result: Dictionary from Weaviate query result

        Returns:
            Dictionary in standard idea format
        """
        return {
            "id": weaviate_result.get("ideaId", ""),
            "title": weaviate_result.get("title", ""),
            "description": weaviate_result.get("description", ""),
            "problem": weaviate_result.get("problem", ""),
            "solution": weaviate_result.get("solution", ""),
            "marketSize": weaviate_result.get("marketSize", ""),
            "tags": weaviate_result.get("tags", []),
            "author": weaviate_result.get("author", ""),
            "createdAt": weaviate_result.get("createdAt", ""),
            "upvotes": weaviate_result.get("upvotes", 0),
            "views": weaviate_result.get("views", 0),
            "status": weaviate_result.get("status", "draft"),
        }

    @staticmethod
    def get_all_ideas(
        search: Optional[str] = None,
        tags: Optional[str] = None,
        sort_by: Optional[str] = "createdAt",
    ) -> List[Dict]:
        """
        Get all ideas from Weaviate with optional filtering and sorting.
        Returns all data from the database to the frontend.

        Args:
            search: Search query to filter ideas by title, description, or problem
            tags: Comma-separated tags to filter by
            sort_by: Field to sort by (createdAt or title)

        Returns:
            List of idea dictionaries with all fields
        """
        # Get all ideas from Weaviate (limit set high to get all data)
        if search:
            # Use Weaviate search with the query
            weaviate_results = weaviate_service.search_ideas(query=search, limit=10000)
        else:
            # Get ALL ideas from Weaviate (no search filter)
            weaviate_results = weaviate_service.search_ideas(query="", limit=10000)

        # Convert Weaviate format to our standard format
        ideas = [
            IdeasService._convert_weaviate_to_idea_format(result)
            for result in weaviate_results
        ]

        # Filter by tags if provided
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            ideas = [
                idea
                for idea in ideas
                if idea.get("id")
                and any(
                    tag in [t.lower() for t in idea.get("tags", [])] for tag in tag_list
                )
            ]

        # Sort ideas
        if sort_by == "title":
            ideas.sort(key=lambda x: x.get("title", "").lower())
        elif sort_by == "createdAt":
            ideas.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        # Return all ideas from Weaviate
        return ideas

    @staticmethod
    def create_idea(idea: IdeaCreate) -> Dict:
        """
        Create a new idea and store it in Weaviate.

        Args:
            idea: IdeaCreate model with idea data

        Returns:
            Dictionary with the created idea data including generated ID
        """
        # Generate unique ID
        idea_id = str(uuid.uuid4())

        # Create idea object
        new_idea = {
            "id": idea_id,
            "title": idea.title,
            "description": idea.description,
            "problem": idea.problem,
            "solution": idea.solution,
            "marketSize": idea.marketSize,
            "tags": idea.tags,
            "author": idea.author,
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "upvotes": 0,
            "views": 0,
            "status": "draft",
        }

        # Add to Weaviate
        weaviate_service.add_idea(new_idea)

        return new_idea

    @staticmethod
    def add_idea(idea_data: Dict) -> Dict:
        """
        Add an idea directly (alternative method for adding ideas).
        This method accepts a dictionary and stores it in Weaviate.

        Args:
            idea_data: Dictionary containing idea data

        Returns:
            Dictionary with the created idea data including generated ID
        """
        # Ensure ID exists
        if "id" not in idea_data:
            idea_id = str(uuid.uuid4())
            idea_data["id"] = idea_id

        # Ensure required fields have defaults
        if "createdAt" not in idea_data:
            idea_data["createdAt"] = datetime.utcnow().isoformat() + "Z"
        if "upvotes" not in idea_data:
            idea_data["upvotes"] = 0
        if "views" not in idea_data:
            idea_data["views"] = 0
        if "status" not in idea_data:
            idea_data["status"] = "draft"

        # Add to Weaviate
        weaviate_service.add_idea(idea_data)

        return idea_data


# Create a singleton instance for easy import
ideas_service = IdeasService()
