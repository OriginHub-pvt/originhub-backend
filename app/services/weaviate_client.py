"""
Weaviate client setup and utilities
"""
import os
import weaviate
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Get Weaviate URL from environment
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")


def get_weaviate_client() -> weaviate.Client:
    """
    Create and return a Weaviate client instance.
    
    Returns:
        weaviate.Client: Configured Weaviate client
    """
    try:
        client = weaviate.Client(
            url=WEAVIATE_URL,
            # Anonymous access is enabled in docker-compose.yml
            # If you add authentication later, use:
            # auth_client_secret=weaviate.AuthApiKey(api_key="your-api-key")
        )
        
        # Test connection
        if not client.is_ready():
            raise ConnectionError(f"Failed to connect to Weaviate at {WEAVIATE_URL}")
        
        return client
    except Exception as e:
        raise ConnectionError(f"Error connecting to Weaviate: {str(e)}")


def create_collection_if_not_exists(
    client: weaviate.Client,
    class_name: str,
    description: str,
    properties: List[Dict[str, Any]]
) -> bool:
    """
    Create a Weaviate collection (class) if it doesn't exist.
    
    Args:
        client: Weaviate client instance
        class_name: Name of the collection/class
        description: Description of the collection
        properties: List of property definitions
        
    Returns:
        bool: True if created, False if already exists
    """
    try:
        # Check if collection exists
        if client.schema.exists(class_name):
            print(f"Collection '{class_name}' already exists")
            return False
        
        # Create collection schema
        class_schema = {
            "class": class_name,
            "description": description,
            "vectorizer": "none",  # No vectorization for now (can add later)
            "properties": properties
        }
        
        client.schema.create_class(class_schema)
        print(f"Collection '{class_name}' created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating collection '{class_name}': {str(e)}")
        raise


# Example: Ideas collection schema
IDEAS_COLLECTION_SCHEMA = {
    "class_name": "Idea",
    "description": "Startup ideas with semantic search capabilities",
    "properties": [
        {
            "name": "ideaId",
            "dataType": ["string"],
            "description": "Unique identifier for the idea"
        },
        {
            "name": "title",
            "dataType": ["string"],
            "description": "Title of the idea"
        },
        {
            "name": "description",
            "dataType": ["text"],
            "description": "Detailed description of the idea"
        },
        {
            "name": "problem",
            "dataType": ["text"],
            "description": "Problem statement the idea solves"
        },
        {
            "name": "solution",
            "dataType": ["text"],
            "description": "Proposed solution"
        },
        {
            "name": "marketSize",
            "dataType": ["string"],
            "description": "Market size category"
        },
        {
            "name": "tags",
            "dataType": ["string[]"],
            "description": "Tags associated with the idea"
        },
        {
            "name": "author",
            "dataType": ["string"],
            "description": "Author of the idea"
        },
        {
            "name": "createdAt",
            "dataType": ["date"],
            "description": "Creation timestamp"
        },
        {
            "name": "upvotes",
            "dataType": ["int"],
            "description": "Number of upvotes"
        },
        {
            "name": "views",
            "dataType": ["int"],
            "description": "Number of views"
        },
        {
            "name": "status",
            "dataType": ["string"],
            "description": "Status of the idea (draft, active, validated, launched)"
        }
    ]
}


def initialize_ideas_collection(client: Optional[weaviate.Client] = None) -> weaviate.Client:
    """
    Initialize the Ideas collection in Weaviate.
    
    Args:
        client: Optional Weaviate client (creates new one if not provided)
        
    Returns:
        weaviate.Client: The client instance
    """
    if client is None:
        client = get_weaviate_client()
    
    create_collection_if_not_exists(
        client=client,
        class_name=IDEAS_COLLECTION_SCHEMA["class_name"],
        description=IDEAS_COLLECTION_SCHEMA["description"],
        properties=IDEAS_COLLECTION_SCHEMA["properties"]
    )
    
    return client

