"""
Comments service layer for business logic
"""

from typing import List, Dict, Optional
from app.models.comment import Comment
from app.models.idea import Idea
from app.schemas.comment import CommentCreate
from app.database import SessionLocal
from datetime import datetime
import uuid


class CommentsService:
    """
    Service layer for comment operations.
    """

    @staticmethod
    def _convert_model_to_dict(comment: Comment, include_replies: bool = False) -> Dict:
        """Convert Comment model to dictionary with datetime objects (not strings)"""
        result = {
            "id": str(comment.id),
            "idea_id": str(comment.idea_id),
            "user_id": comment.user_id,
            "content": comment.content,
            "parent_comment_id": (
                str(comment.parent_comment_id) if comment.parent_comment_id else None
            ),
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "replies": [],
        }

        if include_replies and hasattr(comment, "replies"):
            result["replies"] = [
                CommentsService._convert_model_to_dict(reply, include_replies=True)
                for reply in comment.replies
            ]

        return result

    @staticmethod
    def create_comment(
        idea_id: str, comment_data: CommentCreate, user_id: str
    ) -> Optional[Dict]:
        """
        Create a new comment on an idea or a reply to another comment.

        Args:
            idea_id: UUID of the idea
            comment_data: CommentCreate schema with content and optional parent_comment_id
            user_id: Clerk user ID of the comment author

        Returns:
            Dictionary with comment data, or None if idea not found

        Raises:
            ValueError: If idea doesn't exist or parent comment doesn't exist/belongs to different idea
        """
        db = SessionLocal()
        try:
            # Verify idea exists
            idea = db.query(Idea).filter(Idea.id == idea_id).first()
            if not idea:
                raise ValueError(f"Idea with id {idea_id} not found")

            # If this is a reply, validate the parent comment
            parent_comment_id = comment_data.parent_comment_id
            if parent_comment_id:
                parent_comment = (
                    db.query(Comment).filter(Comment.id == parent_comment_id).first()
                )
                if not parent_comment:
                    raise ValueError(
                        f"Parent comment with id {parent_comment_id} not found"
                    )
                if parent_comment.idea_id != idea_id:
                    raise ValueError(
                        f"Parent comment does not belong to idea {idea_id}. "
                        f"It belongs to idea {parent_comment.idea_id}"
                    )

            # Create comment
            comment = Comment(
                id=str(uuid.uuid4()),
                idea_id=idea_id,
                user_id=user_id,
                content=comment_data.content,
                parent_comment_id=parent_comment_id,
                created_at=datetime.utcnow(),
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)

            return CommentsService._convert_model_to_dict(comment)
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error creating comment: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def get_idea_comments(idea_id: str) -> List[Dict]:
        """
        Get all comments for an idea, organized as a tree structure with nested replies.
        Top-level comments (those without parent_comment_id) are ordered by creation date (newest first).
        Replies are nested under their parent comments.

        Args:
            idea_id: UUID of the idea

        Returns:
            List of comment dictionaries with nested replies (only top-level comments)
        """
        db = SessionLocal()
        try:
            # Get all comments for this idea, eager load replies relationship
            comments = (
                db.query(Comment)
                .filter(Comment.idea_id == idea_id)
                .order_by(Comment.created_at.desc())
                .all()
            )

            # Build a dictionary of all comments by id for quick lookup
            comments_dict = {str(comment.id): comment for comment in comments}

            # Separate top-level comments (no parent) from replies
            top_level_comments = []
            for comment in comments:
                if comment.parent_comment_id is None:
                    top_level_comments.append(comment)

            # Build nested structure by recursively organizing replies
            def build_comment_tree(comment: Comment) -> Dict:
                """Recursively build comment tree with nested replies"""
                comment_dict = CommentsService._convert_model_to_dict(
                    comment, include_replies=False
                )

                # Find all replies to this comment
                replies = [c for c in comments if c.parent_comment_id == comment.id]

                # Recursively build replies tree
                comment_dict["replies"] = [
                    build_comment_tree(reply)
                    for reply in sorted(replies, key=lambda x: x.created_at)
                ]

                return comment_dict

            # Build tree structure for top-level comments
            return [
                build_comment_tree(comment)
                for comment in sorted(
                    top_level_comments, key=lambda x: x.created_at, reverse=True
                )
            ]
        finally:
            db.close()

    @staticmethod
    def get_comment_by_id(comment_id: str) -> Optional[Comment]:
        """
        Get a comment by ID.

        Args:
            comment_id: UUID of the comment

        Returns:
            Comment model or None if not found
        """
        db = SessionLocal()
        try:
            return db.query(Comment).filter(Comment.id == comment_id).first()
        finally:
            db.close()

    @staticmethod
    def delete_comment(comment_id: str, user_id: str) -> bool:
        """
        Delete a comment. Only the comment author or idea owner can delete.

        Args:
            comment_id: UUID of the comment
            user_id: Clerk user ID of the user attempting to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If user doesn't have permission to delete
        """
        db = SessionLocal()
        try:
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                return False

            # Get the idea to check ownership
            idea = db.query(Idea).filter(Idea.id == comment.idea_id).first()
            if not idea:
                return False

            # Check permissions: comment author OR idea owner
            # user_id comes from X-User-Id header (authenticated user)
            # comment.user_id is the user who wrote the comment
            # idea.user_id is the user who owns the idea

            is_comment_author = comment.user_id == user_id
            is_idea_owner = (idea.user_id == user_id) if idea.user_id else False

            if not (is_comment_author or is_idea_owner):
                raise ValueError(
                    "You don't have permission to delete this comment. "
                    "Only the comment author or idea owner can delete comments."
                )

            # Delete the comment
            db.delete(comment)
            db.commit()

            return True
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error deleting comment: {str(e)}")
        finally:
            db.close()


# Create service instance
comments_service = CommentsService()
