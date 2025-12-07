"""
LLM service for AI chat responses
Supports OpenAI API with fallback to mock responses
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize OpenAI client if available
client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def generate_ai_reply(messages_list: List[Dict[str, str]]) -> str:
    """
    Generate AI reply using OpenAI API or fallback to mock response.

    Args:
        messages_list: List of message dictionaries with 'role' and 'content' keys
                     Format: [{"role": "user", "content": "..."}, ...]

    Returns:
        AI response as a string
    """
    # Use OpenAI if available and configured
    if client and OPENAI_API_KEY:
        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_list,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            # Fallback to mock response on error
            return _generate_mock_response(messages_list)

    # Fallback to mock response
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

    Args:
        first_user_message: The first user message text (not formatted conversation)

    Returns:
        Concise title as a string (2-3 words)
    """
    # Use OpenAI if available and configured
    if client and OPENAI_API_KEY:
        try:
            title_prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates very concise titles. Generate a 2-3 word title that summarizes the user's message. Return ONLY the title words, no quotes, no explanation, no additional text. Examples: 'Startup Idea Help', 'Business Advice', 'Product Feedback'.",
                },
                {
                    "role": "user",
                    "content": f"Create a 2-3 word title for this message: {first_user_message}",
                },
            ]
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=title_prompt,
                max_tokens=20,  # Limit response length
                temperature=0.3,  # Lower temperature for more consistent, concise output
            )
            title = response.choices[0].message.content.strip()
            # Clean up the title (remove quotes, extra whitespace, periods)
            title = title.strip().strip('"').strip("'").strip(".").strip()
            # Ensure it's 2-3 words max
            words = title.split()
            if len(words) > 3:
                title = " ".join(words[:3])
            # Limit to 50 characters
            return title[:50] if title else "New Chat"
        except Exception as e:
            print(f"OpenAI API error in title generation: {str(e)}")
            # Fallback to mock title
            return _generate_mock_title(first_user_message)

    # Fallback to mock title generation
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
