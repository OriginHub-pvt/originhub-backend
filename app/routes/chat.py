from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json
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
from app.schemas.chat import ConvertToIdeaRequest
from app.services.chat_service import chat_service
from app.services.llm_service import generate_ai_reply_stream, extract_idea_from_chat
from app.services.ideas_service import ideas_service
from app.schemas import IdeaCreate, IdeaCreateResponse
from app.database import SessionLocal
from app.models.user import User
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def send_message(
    request: MessageCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Send a message in a chat. Creates a new chat if chat_id is not provided.

    If stream=true in request body, returns a streaming response (Server-Sent Events).
    Otherwise, returns a complete response as before.

    Requires authentication via X-User-Id header.
    """
    try:
        user_message = request.message.strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Check if streaming is requested
        if request.stream:
            # Streaming mode: return Server-Sent Events
            return await _handle_streaming_message(
                user_id=user_id,
                chat_id=request.chat_id,
                message=user_message,
            )
        else:
            # Non-streaming mode: return full response
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


async def _handle_streaming_message(
    user_id: str, chat_id: Optional[str], message: str
) -> StreamingResponse:
    """
    Handle streaming message response.

    Creates chat if needed, saves user message, streams AI response,
    then saves the complete AI message.
    """
    # 1. Create chat if not provided
    if not chat_id:
        chat = chat_service.create_chat(user_id)
        chat_id = chat["id"]

    # 2. Save the user message
    chat_service.save_message(chat_id, "user", message)

    # 3. Build history for LLM
    history = chat_service.get_chat_messages(chat_id)
    formatted = [
        {
            "role": "user" if m["sender"] == "user" else "assistant",
            "content": m["message"],
        }
        for m in history
    ]

    # 4. Stream AI response and collect full response
    full_response = ""

    async def generate_stream():
        nonlocal full_response
        try:
            async for token in generate_ai_reply_stream(formatted, chat_id=chat_id):
                full_response += token
                # Format as Server-Sent Events
                chunk_data = json.dumps({"token": token})
                yield f"data: {chunk_data}\n\n"

            # Send final message indicating completion
            yield f"data: {json.dumps({'done': True, 'chat_id': chat_id})}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
        finally:
            # 5. Save the complete AI message after streaming
            if full_response:
                chat_service.save_message(chat_id, "assistant", full_response.strip())

            # 6. Auto-generate title after 2nd message (first user + first assistant)
            messages = chat_service.get_chat_messages(chat_id)
            if len(messages) == 2:
                first_user_message = None
                for msg in messages:
                    if msg["sender"] == "user":
                        first_user_message = msg["message"]
                        break

                if first_user_message:
                    from app.services.llm_service import generate_chat_title

                    title = await generate_chat_title(first_user_message)
                    chat_service.update_chat_title(chat_id, title)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


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


@router.post("/convert-to-idea", response_model=IdeaCreateResponse, status_code=201)
async def convert_chat_to_idea(
    request: ConvertToIdeaRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Convert a chat conversation into a business idea.

    Extracts idea information from all messages in the chat using OpenAI,
    then creates an idea in the database.

    Requires authentication via X-User-Id header.
    Verifies that the chat belongs to the authenticated user.
    """
    try:
        # 1. Get chat_id from request
        chat_id = request.chat_id

        # 2. Verify chat ownership
        chat = chat_service.get_chat_by_id(chat_id, user_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail=f"Chat with id {chat_id} not found or access denied",
            )

        # 3. Get all messages from the chat
        messages = chat_service.get_chat_messages(chat_id)
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="Chat has no messages. Cannot convert empty chat to idea.",
            )

        # 4. Format messages as conversation text
        messages_text = "\n".join(
            [f"{m['sender'].upper()}: {m['message']}" for m in messages]
        )

        # 5. Extract idea information using OpenAI
        idea_data = await extract_idea_from_chat(messages_text)

        # 6. Get user information for author field
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                # Use first_name + last_name if available, otherwise use email
                if user.first_name and user.last_name:
                    author = f"{user.first_name} {user.last_name}"
                elif user.first_name:
                    author = user.first_name
                else:
                    author = user.email.split("@")[0]  # Use email username as fallback
            else:
                # Fallback if user not found
                author = "Unknown"
        finally:
            db.close()

        # 7. Create IdeaCreate object
        idea_create = IdeaCreate(
            title=idea_data["title"],
            description=idea_data["description"],
            problem=idea_data["problem"],
            solution=idea_data["solution"],
            marketSize=idea_data["marketSize"],
            tags=idea_data.get("tags", []),
            author=author,
            link=idea_data.get("link"),
        )

        # 8. Create the idea using the ideas service
        new_idea = ideas_service.create_idea(idea_create, user_id=user_id)

        return IdeaCreateResponse(
            success=True,
            data={"id": new_idea["id"]},
            message="Idea created successfully from chat",
        )

    except HTTPException:
        raise
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
