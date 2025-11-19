from typing import List, Dict, Optional
from app.schemas import IdeaCreate
from app.models.idea import Idea
from app.models.user import User
from app.database import SessionLocal
from sqlalchemy import or_, func
import uuid
from datetime import datetime


class IdeasService:
    """
    Service layer for ideas data operations.
    Uses PostgreSQL database instead of Weaviate.
    """

    @staticmethod
    def _convert_model_to_dict(idea: Idea) -> Dict:
        """
        Convert SQLAlchemy Idea model to dictionary format.

        Args:
            idea: Idea model instance

        Returns:
            Dictionary in standard idea format
        """
        return {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "problem": idea.problem,
            "solution": idea.solution,
            "marketSize": idea.marketSize,
            "tags": idea.tags or [],
            "author": idea.author,
            "createdAt": (
                idea.createdAt.isoformat() + "Z"
                if idea.createdAt
                else datetime.utcnow().isoformat() + "Z"
            ),
            "upvotes": idea.upvotes,
            "views": idea.views,
            "status": idea.status,
            "user_id": idea.user_id,
            "link": idea.link,
        }

    @staticmethod
    def get_all_ideas(
        search: Optional[str] = None,
        tags: Optional[str] = None,
        sort_by: Optional[str] = "createdAt",
    ) -> List[Dict]:
        """
        Get all ideas from PostgreSQL with optional filtering and sorting.
        Returns all data from the database to the frontend.

        Args:
            search: Search query to filter ideas by title, description, or problem
            tags: Comma-separated tags to filter by
            sort_by: Field to sort by (createdAt or title)

        Returns:
            List of idea dictionaries with all fields
        """
        db = SessionLocal()
        try:
            # Start with base query
            query = db.query(Idea)

            # Apply search filter if provided
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Idea.title.ilike(search_pattern),
                        Idea.description.ilike(search_pattern),
                        Idea.problem.ilike(search_pattern),
                        Idea.solution.ilike(search_pattern),
                    )
                )

            # Apply tags filter if provided
            if tags:
                tag_list = [tag.strip().lower() for tag in tags.split(",")]
                # Filter ideas where any tag in the array matches (case-insensitive)
                # Using PostgreSQL array_to_string and ILIKE for case-insensitive matching
                conditions = []
                for tag in tag_list:
                    # Convert array to lowercase string and check if tag is contained
                    conditions.append(
                        func.lower(func.array_to_string(Idea.tags, ",")).contains(tag)
                    )
                if conditions:
                    from sqlalchemy import or_ as sql_or

                    query = query.filter(sql_or(*conditions))

            # Apply sorting
            if sort_by == "title":
                query = query.order_by(Idea.title.asc())
            elif sort_by == "createdAt":
                query = query.order_by(Idea.createdAt.desc())
            else:
                query = query.order_by(Idea.createdAt.desc())

            # Execute query and convert to dictionaries
            ideas = query.all()
            return [IdeasService._convert_model_to_dict(idea) for idea in ideas]

        finally:
            db.close()

    @staticmethod
    def create_idea(idea: IdeaCreate, user_id: Optional[str] = None) -> Dict:
        """
        Create a new idea and store it in PostgreSQL.

        Args:
            idea: IdeaCreate model with idea data
            user_id: Optional user_id to associate with the idea

        Returns:
            Dictionary with the created idea data including generated ID
        """
        db = SessionLocal()
        try:
            # Generate unique ID
            idea_id = str(uuid.uuid4())

            # Create idea object
            new_idea = Idea(
                id=idea_id,
                title=idea.title,
                description=idea.description,
                problem=idea.problem,
                solution=idea.solution,
                marketSize=idea.marketSize,
                tags=idea.tags or [],
                author=idea.author,
                createdAt=datetime.utcnow(),
                upvotes=0,
                views=0,
                status="draft",
                user_id=user_id,
                link=getattr(idea, "link", None),
            )

            # Add to database
            db.add(new_idea)
            db.commit()
            db.refresh(new_idea)

            return IdeasService._convert_model_to_dict(new_idea)

        except Exception as e:
            db.rollback()
            raise Exception(f"Error creating idea: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def add_idea(idea_data: Dict) -> Dict:
        """
        Add an idea directly (alternative method for adding ideas).
        This method accepts a dictionary and stores it in PostgreSQL.

        Args:
            idea_data: Dictionary containing idea data

        Returns:
            Dictionary with the created idea data including generated ID
        """
        db = SessionLocal()
        try:
            # Ensure ID exists and is in correct UUID format
            if "id" not in idea_data:
                idea_id = str(uuid.uuid4())
                idea_data["id"] = idea_id
            else:
                # Validate UUID format
                try:
                    # Try to parse as UUID to ensure it's valid
                    uuid.UUID(idea_data["id"])
                    idea_data["id"] = str(idea_data["id"])  # Ensure it's a string
                except (ValueError, TypeError):
                    # If invalid, generate a new one
                    idea_id = str(uuid.uuid4())
                    idea_data["id"] = idea_id

            # Ensure required fields have defaults
            if "createdAt" not in idea_data:
                idea_data["createdAt"] = datetime.utcnow()
            elif isinstance(idea_data["createdAt"], str):
                # Parse ISO format string to datetime
                try:
                    # Try parsing with Z timezone first
                    if idea_data["createdAt"].endswith("Z"):
                        idea_data["createdAt"] = datetime.fromisoformat(
                            idea_data["createdAt"].replace("Z", "+00:00")
                        )
                    else:
                        idea_data["createdAt"] = datetime.fromisoformat(
                            idea_data["createdAt"]
                        )
                except ValueError:
                    # If parsing fails, use current time
                    idea_data["createdAt"] = datetime.utcnow()
            # If it's already a datetime object, keep it as is

            if "upvotes" not in idea_data:
                idea_data["upvotes"] = 0
            if "views" not in idea_data:
                idea_data["views"] = 0
            if "status" not in idea_data:
                idea_data["status"] = "draft"
            if "tags" not in idea_data:
                idea_data["tags"] = []

            # Ensure tags is a list (not None)
            tags_list = idea_data.get("tags") or []
            if not isinstance(tags_list, list):
                tags_list = []

            # Validate required string fields are not empty
            required_string_fields = [
                "title",
                "description",
                "problem",
                "solution",
                "marketSize",
                "author",
            ]
            for field in required_string_fields:
                if not idea_data.get(field) or not str(idea_data[field]).strip():
                    raise ValueError(f"Field '{field}' cannot be empty")

            # Validate user_id if provided
            user_id = idea_data.get("user_id")
            # Convert empty string, None, or falsy values to None
            if (
                not user_id
                or user_id == ""
                or (isinstance(user_id, str) and not user_id.strip())
            ):
                user_id = None
            else:
                # Check if user exists in database
                user = (
                    db.query(User).filter(User.user_id == str(user_id).strip()).first()
                )
                if not user:
                    # If user doesn't exist, set user_id to None instead of failing
                    # This allows ideas to be created even if user_id is invalid
                    print(
                        f"Warning: user_id '{user_id}' does not exist in users table. Setting to None."
                    )
                    user_id = None

            # Get link field (optional)
            link = idea_data.get("link")
            if link and isinstance(link, str) and not link.strip():
                link = None

            # Create idea object
            new_idea = Idea(
                id=idea_data["id"],
                title=idea_data["title"],
                description=idea_data["description"],
                problem=idea_data["problem"],
                solution=idea_data["solution"],
                marketSize=idea_data["marketSize"],
                tags=tags_list,
                author=idea_data["author"],
                createdAt=idea_data["createdAt"],
                upvotes=idea_data["upvotes"],
                views=idea_data["views"],
                status=idea_data["status"],
                user_id=user_id,
                link=link,
            )

            # Add to database
            db.add(new_idea)
            db.commit()
            db.refresh(new_idea)

            return IdeasService._convert_model_to_dict(new_idea)

        except Exception as e:
            db.rollback()
            # Log the full error for debugging
            import traceback

            error_details = traceback.format_exc()
            print(f"Error adding idea: {str(e)}")
            print(f"Full traceback: {error_details}")
            raise Exception(f"Error adding idea: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def get_idea_by_id(idea_id: str) -> Optional[Dict]:
        """
        Get a single idea by ID from PostgreSQL.

        Args:
            idea_id: UUID of the idea to retrieve

        Returns:
            Dictionary with idea data, or None if not found
        """
        db = SessionLocal()
        try:
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                return None
            return IdeasService._convert_model_to_dict(idea)
        finally:
            db.close()

    @staticmethod
    def update_idea(idea_id: str, update_data: Dict, user_id: str) -> Dict:
        """
        Update an idea in PostgreSQL. Only the owner can update their idea.

        Args:
            idea_id: UUID of the idea to update
            update_data: Dictionary with fields to update (partial updates supported)
            user_id: Clerk user ID of the authenticated user (for ownership check)

        Returns:
            Dictionary with the updated idea data

        Raises:
            ValueError: If idea not found or user is not the owner
        """
        db = SessionLocal()
        try:
            # Get the idea
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                raise ValueError(f"Idea with id {idea_id} not found")

            # Check ownership
            if idea.user_id != user_id:
                raise ValueError("You do not have permission to update this idea")

            # Update allowed fields (partial update)
            allowed_fields = [
                "title",
                "description",
                "problem",
                "solution",
                "marketSize",
                "tags",
                "link",
            ]

            for field in allowed_fields:
                if field in update_data:
                    if field == "marketSize":
                        # Handle camelCase to snake_case conversion
                        setattr(idea, "marketSize", update_data[field])
                    elif field == "tags":
                        # Ensure tags is a list
                        tags_list = update_data[field]
                        if not isinstance(tags_list, list):
                            tags_list = []
                        setattr(idea, "tags", tags_list)
                    else:
                        setattr(idea, field, update_data[field])

            # Commit changes
            db.commit()
            db.refresh(idea)

            return IdeasService._convert_model_to_dict(idea)

        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error updating idea: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def delete_idea(idea_id: str, user_id: str) -> None:
        """
        Delete an idea from PostgreSQL. Only the owner can delete their idea.

        Args:
            idea_id: UUID of the idea to delete
            user_id: Clerk user ID of the authenticated user (for ownership check)

        Raises:
            ValueError: If idea not found or user is not the owner
        """
        db = SessionLocal()
        try:
            # Get the idea
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                raise ValueError(f"Idea with id {idea_id} not found")

            # Check ownership
            if idea.user_id != user_id:
                raise ValueError("You do not have permission to delete this idea")

            # Delete the idea
            db.delete(idea)
            db.commit()

        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error deleting idea: {str(e)}")
        finally:
            db.close()


# Create a singleton instance for easy import
ideas_service = IdeasService()
