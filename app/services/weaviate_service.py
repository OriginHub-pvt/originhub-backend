"""
Weaviate service for vector database operations
"""

from typing import List, Dict, Any, Optional
from app.services.weaviate_client import (
    get_weaviate_client,
    initialize_ideas_collection,
    IDEAS_COLLECTION_SCHEMA,
)


class WeaviateService:
    """
    Service layer for Weaviate vector database operations.
    """

    def __init__(self):
        self.client = get_weaviate_client()
        self.collection_name = IDEAS_COLLECTION_SCHEMA["class_name"]
        # Initialize collection on service creation
        initialize_ideas_collection(self.client)

    def add_idea(self, idea_data: Dict[str, Any]) -> str:
        """
        Add an idea to Weaviate.

        Args:
            idea_data: Dictionary containing idea data

        Returns:
            str: UUID of the created object
        """
        try:
            # Prepare data for Weaviate
            weaviate_object = {
                "ideaId": idea_data.get("id"),
                "title": idea_data.get("title"),
                "description": idea_data.get("description"),
                "problem": idea_data.get("problem"),
                "solution": idea_data.get("solution"),
                "marketSize": idea_data.get("marketSize"),
                "tags": idea_data.get("tags", []),
                "author": idea_data.get("author"),
                "createdAt": idea_data.get("createdAt"),
                "upvotes": idea_data.get("upvotes", 0),
                "views": idea_data.get("views", 0),
                "status": idea_data.get("status", "draft"),
            }

            # Add to Weaviate
            result = self.client.data_object.create(
                data_object=weaviate_object, class_name=self.collection_name
            )

            return result

        except Exception as e:
            raise Exception(f"Error adding idea to Weaviate: {str(e)}")

    def search_ideas(
        self, query: str = "", limit: int = 100, properties: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search ideas using Weaviate's query capabilities.
        If query is empty, returns all ideas.

        Args:
            query: Search query string (empty string returns all)
            limit: Maximum number of results
            properties: List of properties to search in (default: all text properties)

        Returns:
            List of matching ideas
        """
        try:
            # Get all properties we need
            all_properties = [
                "ideaId",
                "title",
                "description",
                "problem",
                "solution",
                "marketSize",
                "tags",
                "author",
                "createdAt",
                "upvotes",
                "views",
                "status",
            ]

            # Build GraphQL query
            query_builder = self.client.query.get(
                self.collection_name, all_properties
            ).with_limit(limit)

            # If query is provided, add a where filter (basic text matching)
            # Note: For semantic/vector search, you'd use .with_near_text() instead
            if query:
                # Simple text search using where filter
                # This searches in title, description, problem, solution
                query_builder = query_builder.with_where(
                    {
                        "operator": "Or",
                        "operands": [
                            {
                                "path": ["title"],
                                "operator": "Like",
                                "valueString": f"*{query}*",
                            },
                            {
                                "path": ["description"],
                                "operator": "Like",
                                "valueString": f"*{query}*",
                            },
                            {
                                "path": ["problem"],
                                "operator": "Like",
                                "valueString": f"*{query}*",
                            },
                            {
                                "path": ["solution"],
                                "operator": "Like",
                                "valueString": f"*{query}*",
                            },
                        ],
                    }
                )

            result = query_builder.do()

            if "data" in result and "Get" in result["data"]:
                ideas = result["data"]["Get"][self.collection_name]
                return ideas

            return []

        except Exception as e:
            raise Exception(f"Error searching ideas in Weaviate: {str(e)}")


# Create singleton instance
weaviate_service = WeaviateService()
