"""
Chat service layer for chat and message operations
Uses PostgreSQL database with SQLAlchemy ORM
"""

from typing import List, Dict, Optional
from app.models.chat import Chat, Message
from app.database import SessionLocal
from datetime import datetime
import uuid
from app.services.llm_service import (
    generate_ai_reply,
    generate_summary,
    generate_chat_title,
)


class ChatService:
    """
    Service layer for chat data operations.
    Uses PostgreSQL database with sync SQLAlchemy operations.
    """

    @staticmethod
    def _convert_chat_to_dict(chat: Chat) -> Dict:
        """Convert SQLAlchemy Chat model to dictionary format."""
        return {
            "id": str(chat.id),
            "user_id": chat.user_id,
            "title": chat.title,
            "created_at": (
                chat.created_at.isoformat() + "Z"
                if chat.created_at
                else datetime.utcnow().isoformat() + "Z"
            ),
            "last_message_at": (
                chat.last_message_at.isoformat() + "Z"
                if chat.last_message_at
                else datetime.utcnow().isoformat() + "Z"
            ),
        }

    @staticmethod
    def _convert_message_to_dict(message: Message) -> Dict:
        """Convert SQLAlchemy Message model to dictionary format."""
        return {
            "id": str(message.id),
            "chat_id": str(message.chat_id),
            "sender": message.sender,
            "message": message.message,
            "created_at": (
                message.created_at.isoformat() + "Z"
                if message.created_at
                else datetime.utcnow().isoformat() + "Z"
            ),
        }

    @staticmethod
    def create_chat(user_id: str) -> Dict:
        """
        Create a new chat for a user.

        Args:
            user_id: Clerk user ID

        Returns:
            Dictionary with the created chat data
        """
        db = SessionLocal()
        try:
            chat_id = str(uuid.uuid4())
            now = datetime.utcnow()

            new_chat = Chat(
                id=chat_id,
                user_id=user_id,
                title=None,
                created_at=now,
                last_message_at=now,
            )

            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            return ChatService._convert_chat_to_dict(new_chat)
        except Exception as e:
            db.rollback()
            raise Exception(f"Error creating chat: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def save_message(chat_id: str, sender: str, message: str) -> Dict:
        """
        Save a message to the database.

        Args:
            chat_id: UUID of the chat
            sender: 'user' or 'assistant'
            message: Message content

        Returns:
            Dictionary with the created message data
        """
        db = SessionLocal()
        try:
            message_id = str(uuid.uuid4())

            new_message = Message(
                id=message_id,
                chat_id=chat_id,
                sender=sender,
                message=message,
                created_at=datetime.utcnow(),
            )

            db.add(new_message)

            # Update chat's last_message_at timestamp
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.last_message_at = datetime.utcnow()

            db.commit()
            db.refresh(new_message)

            return ChatService._convert_message_to_dict(new_message)
        except Exception as e:
            db.rollback()
            raise Exception(f"Error saving message: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def get_chat_messages(chat_id: str) -> List[Dict]:
        """
        Get all messages for a chat, ordered by creation time.

        Args:
            chat_id: UUID of the chat

        Returns:
            List of message dictionaries
        """
        db = SessionLocal()
        try:
            messages = (
                db.query(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.created_at.asc())
                .all()
            )
            return [ChatService._convert_message_to_dict(msg) for msg in messages]
        finally:
            db.close()

    @staticmethod
    def get_user_chats(user_id: str) -> List[Dict]:
        """
        Get all chats for a user, ordered by last message time (most recent first).

        Args:
            user_id: Clerk user ID

        Returns:
            List of chat dictionaries
        """
        db = SessionLocal()
        try:
            chats = (
                db.query(Chat)
                .filter(Chat.user_id == user_id)
                .order_by(Chat.last_message_at.desc())
                .all()
            )
            return [ChatService._convert_chat_to_dict(chat) for chat in chats]
        finally:
            db.close()

    @staticmethod
    def get_empty_chat(user_id: str) -> Optional[Dict]:
        """
        Get the most recent empty chat (chat with no messages) for a user.
        Returns None if no empty chat exists.

        Args:
            user_id: Clerk user ID

        Returns:
            Chat dictionary or None
        """
        db = SessionLocal()
        try:
            # Get all user's chats ordered by creation time (most recent first)
            chats = (
                db.query(Chat)
                .filter(Chat.user_id == user_id)
                .order_by(Chat.created_at.desc())
                .all()
            )

            # Find the first chat with no messages
            for chat in chats:
                message_count = (
                    db.query(Message).filter(Message.chat_id == chat.id).count()
                )
                if message_count == 0:
                    return ChatService._convert_chat_to_dict(chat)

            return None
        finally:
            db.close()

    @staticmethod
    def get_chat_by_id(chat_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get a chat by ID, optionally verifying ownership.

        Args:
            chat_id: UUID of the chat
            user_id: Optional user ID to verify ownership

        Returns:
            Chat dictionary or None if not found
        """
        db = SessionLocal()
        try:
            query = db.query(Chat).filter(Chat.id == chat_id)
            if user_id:
                query = query.filter(Chat.user_id == user_id)

            chat = query.first()
            if not chat:
                return None

            return ChatService._convert_chat_to_dict(chat)
        finally:
            db.close()

    @staticmethod
    def update_chat_title(chat_id: str, title: str) -> None:
        """
        Update the title of a chat.

        Args:
            chat_id: UUID of the chat
            title: New title
        """
        db = SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.title = title
                db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Error updating chat title: {str(e)}")
        finally:
            db.close()

    @staticmethod
    async def process_message(
        user_id: str, chat_id: Optional[str], message: str
    ) -> Dict:
        """
        Process a user message: create chat if needed, save message, get AI reply, save AI message.

        Args:
            user_id: Clerk user ID
            chat_id: Optional chat ID (creates new chat if not provided)
            message: User message content

        Returns:
            Dictionary with chat_id and reply
        """
        # 1. Create chat if not provided
        if not chat_id:
            chat = ChatService.create_chat(user_id)
            chat_id = chat["id"]

        # 2. Save the user message
        ChatService.save_message(chat_id, "user", message)

        # 3. Build history for LLM
        history = ChatService.get_chat_messages(chat_id)
        formatted = [
            {
                "role": "user" if m["sender"] == "user" else "assistant",
                "content": m["message"],
            }
            for m in history
        ]

        # 4. Get AI reply
        ai_response = await generate_ai_reply(formatted)

        # 5. Save AI message
        ChatService.save_message(chat_id, "assistant", ai_response)

        # 6. Auto-generate title after 2nd message (first user + first assistant)
        messages = ChatService.get_chat_messages(chat_id)
        if len(messages) == 2:  # First user message + first assistant response
            # Get first user message only for title generation
            first_user_message = None
            for msg in messages:
                if msg["sender"] == "user":
                    first_user_message = msg["message"]
                    break

            if first_user_message:
                title = await generate_chat_title(first_user_message)
                ChatService.update_chat_title(chat_id, title)

        return {"chat_id": chat_id, "reply": ai_response}

    @staticmethod
    def delete_chat(chat_id: str, user_id: str) -> None:
        """
        Delete a chat and all its messages. Only the owner can delete their chat.
        Messages are automatically deleted due to CASCADE foreign key constraint.

        Args:
            chat_id: UUID of the chat to delete
            user_id: Clerk user ID of the authenticated user (for ownership check)

        Raises:
            ValueError: If chat not found or user is not the owner
        """
        db = SessionLocal()
        try:
            # Get the chat and verify ownership
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                raise ValueError(f"Chat with id {chat_id} not found")

            # Check ownership
            if chat.user_id != user_id:
                raise ValueError("You do not have permission to delete this chat")

            # Delete the chat (messages will be automatically deleted due to CASCADE)
            db.delete(chat)
            db.commit()

        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise Exception(f"Error deleting chat: {str(e)}")
        finally:
            db.close()

    @staticmethod
    async def generate_chat_summary(chat_id: str) -> str:
        """
        Generate a summary for a chat conversation.

        Args:
            chat_id: UUID of the chat

        Returns:
            Summary text
        """
        messages = ChatService.get_chat_messages(chat_id)
        messages_text = "\n".join(
            [f"{m['sender'].upper()}: {m['message']}" for m in messages]
        )
        return await generate_summary(messages_text)


# Create a singleton instance for easy import
chat_service = ChatService()
