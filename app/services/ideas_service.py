from typing import List, Dict, Optional
from app.schemas import IdeaCreate
from app.models.idea import Idea
from app.models.user import User
from app.models.idea_upvote import IdeaUpvote
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

            # Calculate upvote counts from idea_upvotes table for accuracy
            # Also sync the column value for future queries
            idea_dicts = []
            for idea in ideas:
                idea_dict = IdeasService._convert_model_to_dict(idea)
                # Calculate actual upvote count from table
                actual_upvote_count = (
                    db.query(func.count(IdeaUpvote.id))
                    .filter(IdeaUpvote.idea_id == idea.id)
                    .scalar()
                ) or 0

                # Sync the column value if it's different (for future queries)
                if idea.upvotes != actual_upvote_count:
                    idea.upvotes = actual_upvote_count

                # Update the upvote count in the returned data
                idea_dict["upvotes"] = actual_upvote_count
                idea_dicts.append(idea_dict)

            # Commit any column updates
            db.commit()

            return idea_dicts

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
        Calculates upvote count from idea_upvotes table for accuracy.

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

            idea_dict = IdeasService._convert_model_to_dict(idea)

            # Calculate actual upvote count from table for accuracy
            actual_upvote_count = (
                db.query(func.count(IdeaUpvote.id))
                .filter(IdeaUpvote.idea_id == idea_id)
                .scalar()
            ) or 0

            # Sync the column value if it's different (for future queries)
            if idea.upvotes != actual_upvote_count:
                idea.upvotes = actual_upvote_count
                db.commit()

            # Update the upvote count in the returned data
            idea_dict["upvotes"] = actual_upvote_count

            return idea_dict
        finally:
            db.close()

    @staticmethod
    def increment_views(idea_id: str) -> Optional[Dict]:
        """
        Increment the view count for an idea by 1.

        Args:
            idea_id: UUID of the idea

        Returns:
            Dictionary with updated idea data, or None if not found
        """
        db = SessionLocal()
        try:
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                return None

            # Increment views
            idea.views += 1
            db.commit()
            db.refresh(idea)

            return IdeasService._convert_model_to_dict(idea)
        except Exception as e:
            db.rollback()
            raise Exception(f"Error incrementing views: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def has_user_upvoted(idea_id: str, user_id: str) -> bool:
        """
        Check if a user has already upvoted an idea.

        Args:
            idea_id: UUID of the idea
            user_id: Clerk user ID

        Returns:
            True if user has upvoted, False otherwise
        """
        db = SessionLocal()
        try:
            upvote = (
                db.query(IdeaUpvote)
                .filter(IdeaUpvote.idea_id == idea_id, IdeaUpvote.user_id == user_id)
                .first()
            )
            return upvote is not None
        finally:
            db.close()

    @staticmethod
    def _sync_upvote_count(db, idea_id: str) -> int:
        """
        Calculate and sync the upvote count for an idea from the idea_upvotes table.
        Updates the ideas.upvotes column to match the actual count.

        Args:
            db: Database session
            idea_id: UUID of the idea

        Returns:
            The actual upvote count
        """
        # Count upvotes from the table
        actual_count = (
            db.query(func.count(IdeaUpvote.id))
            .filter(IdeaUpvote.idea_id == idea_id)
            .scalar()
        ) or 0

        # Update the idea's upvote count
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            idea.upvotes = actual_count

        return actual_count

    @staticmethod
    def increment_upvotes(idea_id: str, user_id: str) -> Optional[Dict]:
        """
        Add an upvote for an idea by a user.
        Creates an upvote record in idea_upvotes table and syncs the count.
        Prevents duplicate upvotes from the same user.

        Args:
            idea_id: UUID of the idea
            user_id: Clerk user ID

        Returns:
            Dictionary with updated idea data, or None if not found

        Raises:
            ValueError: If user has already upvoted this idea
        """
        db = SessionLocal()
        try:
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                return None

            # Check if user already upvoted
            existing_upvote = (
                db.query(IdeaUpvote)
                .filter(IdeaUpvote.idea_id == idea_id, IdeaUpvote.user_id == user_id)
                .first()
            )

            if existing_upvote:
                raise ValueError("User has already upvoted this idea")

            # Create upvote record
            upvote = IdeaUpvote(
                id=str(uuid.uuid4()),
                user_id=user_id,
                idea_id=idea_id,
                created_at=datetime.utcnow(),
            )
            db.add(upvote)

            # Sync upvote count from table (ensures accuracy)
            IdeasService._sync_upvote_count(db, idea_id)

            db.commit()
            db.refresh(idea)

            return IdeasService._convert_model_to_dict(idea)
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error incrementing upvotes: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def decrement_upvotes(idea_id: str, user_id: str) -> Optional[Dict]:
        """
        Remove an upvote for an idea by a user.
        Deletes the upvote record from idea_upvotes table and syncs the count.

        Args:
            idea_id: UUID of the idea
            user_id: Clerk user ID

        Returns:
            Dictionary with updated idea data, or None if not found

        Raises:
            ValueError: If user has not upvoted this idea
        """
        db = SessionLocal()
        try:
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                return None

            # Find and delete upvote record
            upvote = (
                db.query(IdeaUpvote)
                .filter(IdeaUpvote.idea_id == idea_id, IdeaUpvote.user_id == user_id)
                .first()
            )

            if not upvote:
                raise ValueError("User has not upvoted this idea")

            # Delete upvote record
            db.delete(upvote)

            # Sync upvote count from table (ensures accuracy)
            IdeasService._sync_upvote_count(db, idea_id)

            db.commit()
            db.refresh(idea)

            return IdeasService._convert_model_to_dict(idea)
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error decrementing upvotes: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def get_user_upvoted_ideas(user_id: str) -> List[str]:
        """
        Get list of idea IDs that a user has upvoted.

        Args:
            user_id: Clerk user ID

        Returns:
            List of idea IDs (UUIDs as strings)
        """
        db = SessionLocal()
        try:
            upvotes = db.query(IdeaUpvote).filter(IdeaUpvote.user_id == user_id).all()
            return [str(upvote.idea_id) for upvote in upvotes]
        finally:
            db.close()

    @staticmethod
    def sync_all_upvote_counts() -> Dict[str, int]:
        """
        Recalculate and sync upvote counts for all ideas from the idea_upvotes table.
        Useful for data integrity checks or after migrations.

        Returns:
            Dictionary mapping idea_id to upvote count
        """
        db = SessionLocal()
        try:
            # Get all ideas
            ideas = db.query(Idea).all()
            synced_counts = {}

            for idea in ideas:
                actual_count = IdeasService._sync_upvote_count(db, idea.id)
                synced_counts[str(idea.id)] = actual_count

            db.commit()
            return synced_counts
        except Exception as e:
            db.rollback()
            raise Exception(f"Error syncing upvote counts: {str(e)}")
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
