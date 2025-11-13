from typing import List, Optional, Dict
from app.models import IdeaCreate
import uuid
from datetime import datetime
from app.services.weaviate_service import weaviate_service

# In-memory storage for ideas
# TODO: Replace with database connection when ready
_ideas_storage: List[Dict] = [
    {
        "id": "1",
        "title": "AI-Powered Food Waste Reduction Platform",
        "description": "A smart platform that connects restaurants, grocery stores, and consumers to reduce food waste through AI-driven inventory management and donation matching.",
        "problem": "Food waste is a massive global problem, with 1.3 billion tons of food wasted annually, causing environmental and economic damage.",
        "solution": "An AI-powered platform that predicts food waste, matches surplus food with donation centers, and optimizes inventory management for businesses.",
        "marketSize": "Large",
        "tags": ["AI", "Sustainability", "Food Tech", "Social Impact"],
        "author": "Sarah Johnson",
        "createdAt": "2024-01-15T10:30:00Z",
        "upvotes": 234,
        "views": 1200,
        "status": "active",
    },
    {
        "id": "2",
        "title": "Remote Team Wellness Assistant",
        "description": "A comprehensive wellness platform designed for remote teams, offering mental health support, virtual team building, and productivity optimization tools.",
        "problem": "Remote workers face isolation, burnout, and lack of work-life balance, leading to decreased productivity and mental health issues.",
        "solution": "A platform providing personalized wellness programs, virtual team activities, and AI-driven stress management tools for remote teams.",
        "marketSize": "Medium",
        "tags": ["Remote Work", "Health Tech", "SaaS", "B2B"],
        "author": "Mike Chen",
        "createdAt": "2024-01-20T14:20:00Z",
        "upvotes": 189,
        "views": 890,
        "status": "validated",
    },
    {
        "id": "3",
        "title": "Blockchain-Based Supply Chain Transparency",
        "description": "A blockchain solution that provides end-to-end transparency in supply chains, helping consumers verify product authenticity and ethical sourcing.",
        "problem": "Consumers lack visibility into supply chains, making it difficult to verify product authenticity, ethical sourcing, and environmental impact.",
        "solution": "A blockchain platform that tracks products from origin to consumer, providing immutable records of authenticity, sourcing, and sustainability metrics.",
        "marketSize": "Large",
        "tags": ["Blockchain", "Supply Chain", "Sustainability", "B2B2C"],
        "author": "Alex Rivera",
        "createdAt": "2024-01-18T09:15:00Z",
        "upvotes": 312,
        "views": 1500,
        "status": "active",
    },
    {
        "id": "4",
        "title": "Personalized Learning Path Generator",
        "description": "An AI-driven educational platform that creates personalized learning paths for students based on their learning style, pace, and career goals.",
        "problem": "Traditional education uses a one-size-fits-all approach, failing to accommodate individual learning styles and career aspirations.",
        "solution": "An AI platform that analyzes learning patterns, creates customized curricula, and adapts in real-time to optimize student outcomes.",
        "marketSize": "Medium",
        "tags": ["EdTech", "AI", "Personalization", "B2C"],
        "author": "Emily Wang",
        "createdAt": "2024-01-22T11:45:00Z",
        "upvotes": 156,
        "views": 670,
        "status": "draft",
    },
    {
        "id": "5",
        "title": "Smart Home Energy Optimization System",
        "description": "An IoT-based energy management system that optimizes home energy consumption using AI, reducing costs and carbon footprint.",
        "problem": "Homeowners waste energy due to inefficient heating, cooling, and appliance usage, leading to high costs and environmental impact.",
        "solution": "An IoT system with AI algorithms that learns usage patterns and automatically optimizes energy consumption while maintaining comfort.",
        "marketSize": "Large",
        "tags": ["IoT", "Energy", "AI", "Smart Home"],
        "author": "David Kim",
        "createdAt": "2024-01-19T16:30:00Z",
        "upvotes": 278,
        "views": 1100,
        "status": "launched",
    },
    {
        "id": "6",
        "title": "Mental Health Chatbot for Students",
        "description": "A 24/7 AI-powered mental health chatbot specifically designed for students, providing instant support, resources, and crisis intervention.",
        "problem": "Students face mental health challenges but often lack access to affordable, timely support, especially during crisis situations.",
        "solution": "An AI chatbot that provides immediate mental health support, connects students with resources, and escalates to human professionals when needed.",
        "marketSize": "Medium",
        "tags": ["Mental Health", "AI", "Education", "Healthcare"],
        "author": "Jessica Martinez",
        "createdAt": "2024-01-21T12:10:00Z",
        "upvotes": 201,
        "views": 950,
        "status": "active",
    },
]


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
        Falls back to in-memory storage if Weaviate is unavailable.
        
        Args:
            search: Search query to filter ideas by title, description, or problem
            tags: Comma-separated tags to filter by
            sort_by: Field to sort by (createdAt or title)
            
        Returns:
            List of idea dictionaries with all fields
        """
        try:
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
                    if idea.get("id") and any(
                        tag in [t.lower() for t in idea.get("tags", [])]
                        for tag in tag_list
                    )
                ]
            
            # Sort ideas
            if sort_by == "title":
                ideas.sort(key=lambda x: x.get("title", "").lower())
            elif sort_by == "createdAt":
                ideas.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            
            # Return all ideas from Weaviate
            return ideas
            
        except Exception as e:
            # Fallback to in-memory storage if Weaviate fails
            print(f"Warning: Failed to get ideas from Weaviate: {str(e)}")
            print("Falling back to in-memory storage")
            
            filtered_ideas = _ideas_storage.copy()

            # Filter by search query
            if search:
                search_lower = search.lower()
                filtered_ideas = [
                    idea
                    for idea in filtered_ideas
                    if search_lower in idea["title"].lower()
                    or search_lower in idea["description"].lower()
                    or search_lower in idea["problem"].lower()
                ]

            # Filter by tags
            if tags:
                tag_list = [tag.strip().lower() for tag in tags.split(",")]
                filtered_ideas = [
                    idea
                    for idea in filtered_ideas
                    if any(tag in [t.lower() for t in idea["tags"]] for tag in tag_list)
                ]

            # Sort ideas
            if sort_by == "title":
                filtered_ideas.sort(key=lambda x: x["title"].lower())
            elif sort_by == "createdAt":
                filtered_ideas.sort(key=lambda x: x["createdAt"], reverse=True)

            return filtered_ideas

    @staticmethod
    def get_idea_by_id(idea_id: str) -> Optional[Dict]:
        """
        Get a single idea by ID.
        
        Args:
            idea_id: The ID of the idea to retrieve
            
        Returns:
            Idea dictionary if found, None otherwise
        """
        for idea in _ideas_storage:
            if idea["id"] == idea_id:
                return idea
        return None

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
        try:
            weaviate_service.add_idea(new_idea)
        except Exception as e:
            # Fallback to in-memory storage if Weaviate fails
            print(f"Warning: Failed to add idea to Weaviate: {str(e)}")
            print("Falling back to in-memory storage")
            _ideas_storage.append(new_idea)

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
        try:
            weaviate_service.add_idea(idea_data)
        except Exception as e:
            # Fallback to in-memory storage if Weaviate fails
            print(f"Warning: Failed to add idea to Weaviate: {str(e)}")
            print("Falling back to in-memory storage")
            _ideas_storage.append(idea_data)
        
        return idea_data

    @staticmethod
    def update_idea(idea_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update an existing idea.
        
        Args:
            idea_id: The ID of the idea to update
            updates: Dictionary with fields to update
            
        Returns:
            Updated idea dictionary if found, None otherwise
        """
        for idea in _ideas_storage:
            if idea["id"] == idea_id:
                idea.update(updates)
                return idea
        return None

    @staticmethod
    def delete_idea(idea_id: str) -> bool:
        """
        Delete an idea by ID.
        
        Args:
            idea_id: The ID of the idea to delete
            
        Returns:
            True if deleted, False if not found
        """
        for i, idea in enumerate(_ideas_storage):
            if idea["id"] == idea_id:
                _ideas_storage.pop(i)
                return True
        return False


# Create a singleton instance for easy import
ideas_service = IdeasService()

