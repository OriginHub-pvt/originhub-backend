from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ChatSendResponse,
    ChatSummaryResponse,
    ChatDeleteResponse,
)
from app.services.chat_service import chat_service
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatSendResponse)
async def send_message(
    request: MessageCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Send a message in a chat. Creates a new chat if chat_id is not provided.

    Requires authentication via X-User-Id header.
    """
    try:
        user_message = request.message.strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Process the message (creates chat if needed, gets AI reply)
        result = await chat_service.process_message(
            user_id=user_id,
            chat_id=request.chat_id,
            message=user_message,
        )

        return ChatSendResponse(
            success=True,
            data={
                "chat_id": result["chat_id"],
                "reply": result["reply"],
            },
            message="Message sent successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/empty", response_model=ChatResponse)
async def get_or_create_empty_chat(user_id: str = Depends(get_current_user_id)):
    """
    Get an empty chat for the user. Reuses existing empty chat if available,
    otherwise creates a new one. This prevents creating multiple empty chats.

    Requires authentication via X-User-Id header.
    Returns an empty chat (chat with no messages) that can be used for sending messages.
    """
    try:
        # First, try to find an existing empty chat
        empty_chat = chat_service.get_empty_chat(user_id)

        if empty_chat:
            # Return existing empty chat
            return ChatResponse(
                id=empty_chat["id"],
                user_id=empty_chat["user_id"],
                title=empty_chat["title"],
                created_at=empty_chat["created_at"],
                last_message_at=empty_chat["last_message_at"],
            )
        else:
            # No empty chat exists, create a new one
            chat = chat_service.create_chat(user_id)
            return ChatResponse(
                id=chat["id"],
                user_id=chat["user_id"],
                title=chat["title"],
                created_at=chat["created_at"],
                last_message_at=chat["last_message_at"],
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/new", response_model=ChatResponse, status_code=201)
async def create_new_chat(user_id: str = Depends(get_current_user_id)):
    """
    Create a new empty chat for the authenticated user.
    Note: Consider using GET /chat/empty instead to reuse existing empty chats.

    Requires authentication via X-User-Id header.
    Returns the created chat with chat_id that can be used for sending messages.
    """
    try:
        chat = chat_service.create_chat(user_id)

        return ChatResponse(
            id=chat["id"],
            user_id=chat["user_id"],
            title=chat["title"],
            created_at=chat["created_at"],
            last_message_at=chat["last_message_at"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/list", response_model=ChatListResponse)
async def list_user_chats(user_id: str = Depends(get_current_user_id)):
    """
    Get all chats for the authenticated user.

    Requires authentication via X-User-Id header.
    """
    try:
        chats = chat_service.get_user_chats(user_id)

        return ChatListResponse(
            success=True,
            data={"chats": chats},
            message=f"Retrieved {len(chats)} chats",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def list_messages(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get all messages for a specific chat.

    Requires authentication via X-User-Id header.
    Verifies that the chat belongs to the authenticated user.
    """
    try:
        # Verify chat ownership
        chat = chat_service.get_chat_by_id(chat_id, user_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail=f"Chat with id {chat_id} not found or access denied",
            )

        messages = chat_service.get_chat_messages(chat_id)

        return MessageListResponse(
            success=True,
            data={"messages": messages},
            message=f"Retrieved {len(messages)} messages",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{chat_id}/summary", response_model=ChatSummaryResponse)
async def summarize_chat(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Generate a summary for a chat conversation.

    Requires authentication via X-User-Id header.
    Verifies that the chat belongs to the authenticated user.
    """
    try:
        # Verify chat ownership
        chat = chat_service.get_chat_by_id(chat_id, user_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail=f"Chat with id {chat_id} not found or access denied",
            )

        summary = await chat_service.generate_chat_summary(chat_id)

        return ChatSummaryResponse(
            success=True,
            data={"chat_id": chat_id, "summary": summary},
            message="Summary generated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{chat_id}", response_model=ChatDeleteResponse, status_code=200)
async def delete_chat(chat_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Delete a chat and all its messages. Only the owner can delete their chat.

    Messages are automatically deleted due to CASCADE foreign key constraint.
    Requires authentication via X-User-Id header.
    Returns 403 Forbidden if the user is not the owner.
    Returns 404 Not Found if the chat doesn't exist.
    """
    try:
        # Delete the chat (service will check ownership)
        chat_service.delete_chat(chat_id=chat_id, user_id=user_id)

        return ChatDeleteResponse(success=True, message="Chat deleted successfully")

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


# Legacy endpoint for backward compatibility
@router.post("/legacy", response_model=ChatSendResponse)
async def chat_legacy(
    request: ChatRequest, user_id: str = Depends(get_current_user_id)
):
    """
    Legacy chat endpoint - receives user message and returns AI response.
    Use POST /chat instead with MessageCreate schema.
    """
    try:
        user_message = request.message.strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Process the message (creates new chat)
        result = await chat_service.process_message(
            user_id=user_id,
            chat_id=None,
            message=user_message,
        )

        return ChatSendResponse(
            success=True,
            data={
                "chat_id": result["chat_id"],
                "reply": result["reply"],
            },
            message="Chat response generated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
