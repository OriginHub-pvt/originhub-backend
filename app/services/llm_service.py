"""
LLM service for AI chat responses
Uses local OriginHub Agentic System API (localhost:8004) for user conversations
"""

import os
from typing import List, Dict, Optional, AsyncGenerator
from dotenv import load_dotenv
import httpx
import json
import asyncio

load_dotenv()

# Try to import OpenAI for idea extraction
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Get OpenAI API key from environment (for idea extraction)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize OpenAI client if available
openai_client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Configuration for local API
API_BASE_URL = os.getenv("ORIGINHUB_API_URL", "http://localhost:8004")
API_HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
API_CREATE_SESSION_ENDPOINT = f"{API_BASE_URL}/sessions"
API_CHAT_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/chat"
API_DELETE_SESSION_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/sessions"

# Session management: maps chat_id to session_id
# In production, you might want to store this in the database
_chat_to_session_map: Dict[str, str] = {}

# HTTP client for async requests
_http_client: Optional[httpx.AsyncClient] = None


async def _get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client for API requests."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


async def _check_api_health() -> bool:
    """Check if the local API is running and healthy."""
    try:
        client = await _get_http_client()
        response = await client.get(API_HEALTH_ENDPOINT, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        print(f"API health check failed: {str(e)}")
        return False


async def _create_session() -> Optional[str]:
    """Create a new session in the local API."""
    try:
        client = await _get_http_client()
        response = await client.post(API_CREATE_SESSION_ENDPOINT, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_id")
        else:
            print(f"Failed to create session: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return None


async def _get_or_create_session(chat_id: str) -> Optional[str]:
    """
    Get existing session_id for a chat_id or create a new one.

    This function is called lazily when the first message is sent for a chat.
    The session is NOT created when the chat is created in the database.
    This ensures we only create API sessions when they're actually needed.

    Args:
        chat_id: The database chat ID (UUID)

    Returns:
        The API session_id if successful, None otherwise
    """
    if chat_id in _chat_to_session_map:
        return _chat_to_session_map[chat_id]

    # Create a new session in the API (this happens on first message, not on chat creation)
    session_id = await _create_session()
    if session_id:
        _chat_to_session_map[chat_id] = session_id
    return session_id


async def _delete_session(session_id: str) -> None:
    """Delete a session from the local API."""
    try:
        client = await _get_http_client()
        await client.delete(
            f"{API_DELETE_SESSION_ENDPOINT_TEMPLATE}/{session_id}", timeout=5.0
        )
    except Exception as e:
        print(f"Error deleting session: {str(e)}")


def cleanup_chat_session(chat_id: str) -> None:
    """
    Clean up session mapping when a chat is deleted.
    This should be called when a chat is deleted to remove the session mapping.

    Args:
        chat_id: The chat ID to clean up
    """
    if chat_id in _chat_to_session_map:
        session_id = _chat_to_session_map.pop(chat_id)
        # Optionally delete the session from the API as well
        # Note: This is a sync function, so we can't await the delete
        # The session will be cleaned up by the API eventually if not used


async def generate_ai_reply(
    messages_list: List[Dict[str, str]], chat_id: Optional[str] = None
) -> str:
    """
    Generate AI reply using local OriginHub Agentic System API.

    Args:
        messages_list: List of message dictionaries with 'role' and 'content' keys
                     Format: [{"role": "user", "content": "..."}, ...]
        chat_id: Optional chat ID for session management. If provided, maintains
                session state across messages. If not provided, creates a new session
                for each call.

    Returns:
        AI response as a string
    """
    # Check API health first
    if not await _check_api_health():
        print("Local API is not available, falling back to mock response")
        return _generate_mock_response(messages_list)

    # Extract the last user message (the API manages conversation state via sessions)
    # Note: We only send the current message, not the full history, because the API
    # maintains conversation context within each session. This matches the Streamlit app pattern.
    last_user_message = None
    for msg in reversed(messages_list):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        return "I'm here to help! What would you like to discuss?"

    try:
        # Get or create session for this chat
        # IMPORTANT: Session is created lazily here (on first message), NOT when chat is created in DB
        # This ensures we only create API sessions when actually needed for conversation
        session_id = None
        if chat_id:
            session_id = await _get_or_create_session(chat_id)
        else:
            # If no chat_id provided, create a temporary session (will be cleaned up after use)
            session_id = await _create_session()

        if not session_id:
            print("Failed to create/get session, falling back to mock response")
            return _generate_mock_response(messages_list)

        # Send message to the API
        client = await _get_http_client()
        payload = {"message": last_user_message}

        response = await client.post(
            f"{API_CHAT_ENDPOINT_TEMPLATE}/{session_id}", json=payload, timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            ai_response_raw = data.get("response", "")

            # The API may return response as string or dict, convert dict to string if needed
            if isinstance(ai_response_raw, dict):
                # If it's a dict, try to extract meaningful text or convert to JSON string
                if "text" in ai_response_raw:
                    ai_response = ai_response_raw["text"]
                elif "message" in ai_response_raw:
                    ai_response = ai_response_raw["message"]
                elif "content" in ai_response_raw:
                    ai_response = ai_response_raw["content"]
                else:
                    # Convert dict to JSON string as fallback
                    import json

                    ai_response = json.dumps(ai_response_raw)
            else:
                ai_response = str(ai_response_raw) if ai_response_raw else ""

            # If no chat_id was provided and we created a temp session, clean it up
            if not chat_id and session_id:
                await _delete_session(session_id)

            return (
                ai_response if ai_response else _generate_mock_response(messages_list)
            )
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return _generate_mock_response(messages_list)

    except httpx.TimeoutException:
        print("Request to local API timed out, falling back to mock response")
        return _generate_mock_response(messages_list)
    except Exception as e:
        print(f"Error calling local API: {str(e)}")
        return _generate_mock_response(messages_list)


def _generate_mock_response(messages_list: List[Dict[str, str]]) -> str:
    """
    Generate a mock AI response for development/testing.

    Args:
        messages_list: List of message dictionaries

    Returns:
        Mock AI response
    """
    if not messages_list:
        return "Hello! How can I help you today?"

    # Get the last user message
    last_user_message = None
    for msg in reversed(messages_list):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if last_user_message:
        return f"I understand you're asking about: {last_user_message}. Let me help you brainstorm some solutions and ideas. What specific aspect would you like to explore further?"
    else:
        return "I'm here to help! What would you like to discuss?"


async def generate_ai_reply_stream(
    messages_list: List[Dict[str, str]], chat_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream AI reply using local OriginHub Agentic System API.
    Yields tokens as they're generated (chunked from full response).

    Args:
        messages_list: List of message dictionaries with 'role' and 'content' keys
                     Format: [{"role": "user", "content": "..."}, ...]
        chat_id: Optional chat ID for session management. If provided, maintains
                session state across messages. If not provided, creates a new session
                for each call.

    Yields:
        Tokens/chunks of the AI response as strings
    """
    # Check API health first
    if not await _check_api_health():
        print("Local API is not available, falling back to mock response")
        mock_response = _generate_mock_response(messages_list)
        # Stream the mock response word by word
        for word in mock_response.split():
            yield word + " "
        return

    # Extract the last user message
    last_user_message = None
    for msg in reversed(messages_list):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        yield "I'm here to help! What would you like to discuss?"
        return

    try:
        # Get or create session for this chat
        session_id = None
        if chat_id:
            session_id = await _get_or_create_session(chat_id)
        else:
            session_id = await _create_session()

        if not session_id:
            print("Failed to create/get session, falling back to mock response")
            mock_response = _generate_mock_response(messages_list)
            for word in mock_response.split():
                yield word + " "
            return

        # Send message to the API
        client = await _get_http_client()
        payload = {"message": last_user_message}

        response = await client.post(
            f"{API_CHAT_ENDPOINT_TEMPLATE}/{session_id}", json=payload, timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            ai_response_raw = data.get("response", "")

            # The API may return response as string or dict, convert dict to string if needed
            if isinstance(ai_response_raw, dict):
                if "text" in ai_response_raw:
                    ai_response = ai_response_raw["text"]
                elif "message" in ai_response_raw:
                    ai_response = ai_response_raw["message"]
                elif "content" in ai_response_raw:
                    ai_response = ai_response_raw["content"]
                else:
                    import json

                    ai_response = json.dumps(ai_response_raw)
            else:
                ai_response = str(ai_response_raw) if ai_response_raw else ""

            # Stream the response word by word (simulating token streaming)
            # In a real streaming API, you'd stream actual tokens as they're generated
            if ai_response:
                # Split into words and stream with small delay for realistic streaming effect
                words = ai_response.split()
                for i, word in enumerate(words):
                    if i > 0:
                        yield " "  # Add space before word (except first)
                    yield word
                    # Small delay to simulate real streaming (optional, can be removed)
                    await asyncio.sleep(0.01)
            else:
                # Fallback to mock if empty
                mock_response = _generate_mock_response(messages_list)
                for word in mock_response.split():
                    yield word + " "
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            mock_response = _generate_mock_response(messages_list)
            for word in mock_response.split():
                yield word + " "

    except httpx.TimeoutException:
        print("Request to local API timed out, falling back to mock response")
        mock_response = _generate_mock_response(messages_list)
        for word in mock_response.split():
            yield word + " "
    except Exception as e:
        print(f"Error calling local API: {str(e)}")
        mock_response = _generate_mock_response(messages_list)
        for word in mock_response.split():
            yield word + " "


async def generate_summary(messages_text: str) -> str:
    """
    Generate a summary of a conversation.

    Args:
        messages_text: Formatted conversation text

    Returns:
        Summary as a string
    """
    summary_prompt = [
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversations clearly and concisely. Provide a brief summary in 1-2 sentences.",
        },
        {"role": "user", "content": f"Summarize this conversation:\n\n{messages_text}"},
    ]

    return await generate_ai_reply(summary_prompt)


async def generate_chat_title(first_user_message: str) -> str:
    """
    Generate a concise 2-3 word title from the first user message.
    Uses simple extraction from the message text.

    Args:
        first_user_message: The first user message text (not formatted conversation)

    Returns:
        Concise title as a string (2-3 words)
    """
    # Use simple title generation from the message
    # This is more reliable and doesn't require API calls
    return _generate_mock_title(first_user_message)


def _generate_mock_title(first_user_message: str) -> str:
    """
    Generate a simple mock title from the first user message.
    Creates a 2-3 word title from the first few words.

    Args:
        first_user_message: The first user message text

    Returns:
        Simple 2-3 word title string
    """
    if not first_user_message or not first_user_message.strip():
        return "New Chat"

    # Extract first 2-3 words from the message
    words = first_user_message.strip().split()[:3]
    title = " ".join(words)

    # Limit to 50 characters
    if len(title) > 50:
        title = title[:47] + "..."

    return title if title else "New Chat"


async def extract_idea_from_chat(messages_text: str) -> Dict[str, str]:
    """
    Extract idea information from chat conversation using OpenAI.

    Args:
        messages_text: Full conversation text from chat messages

    Returns:
        Dictionary with idea fields: title, description, problem, solution, marketSize, tags, link
    """
    if not openai_client or not OPENAI_API_KEY:
        raise Exception(
            "OpenAI API is not configured. Please set OPENAI_API_KEY environment variable."
        )

    extraction_prompt = f"""Extract business idea information from the following conversation and return it as a JSON object with these exact fields:
- title: A concise title for the idea (2-5 words)
- description: A brief description of the idea (2-3 sentences)
- problem: The problem this idea solves (1-2 sentences)
- solution: The proposed solution (2-3 sentences)
- marketSize: Market size in Large, Medium, Small
- tags: Array of relevant tags (3-5 tags, lowercase, no spaces use hyphens)
- link: Any URL mentioned in the conversation, or null if none

Conversation:
{messages_text}

Return ONLY valid JSON in this exact format:
{{
  "title": "...",
  "description": "...",
  "problem": "...",
  "solution": "...",
  "marketSize": "...",
  "tags": ["tag1", "tag2", "tag3"],
  "link": "..." or null
}}"""

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured business idea information from conversations. Always return valid JSON only, no additional text.",
                },
                {"role": "user", "content": extraction_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        idea_data = json.loads(result_text)

        # Ensure all required fields are present and tags is a list
        required_fields = ["title", "description", "problem", "solution", "marketSize"]
        for field in required_fields:
            if field not in idea_data or not idea_data[field]:
                raise ValueError(f"Missing or empty required field: {field}")

        # Ensure tags is a list
        if "tags" not in idea_data:
            idea_data["tags"] = []
        if not isinstance(idea_data["tags"], list):
            idea_data["tags"] = []

        # Ensure link is string or None
        if "link" not in idea_data:
            idea_data["link"] = None
        if idea_data["link"] and not isinstance(idea_data["link"], str):
            idea_data["link"] = None

        return idea_data

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse OpenAI response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Error extracting idea from chat: {str(e)}")
