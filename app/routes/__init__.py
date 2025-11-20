"""
Routes package - Centralized router configuration
All API routes are registered here and then included in main.py
"""

from fastapi import APIRouter
from app.routes import chat, ideas, webhooks, websocket

# Create a main API router that combines all route modules
# Note: Individual routers already have /api prefix, so no prefix here
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(chat.router)
api_router.include_router(ideas.router)
api_router.include_router(webhooks.router)
api_router.include_router(websocket.router)

# Export for use in main.py
__all__ = ["api_router"]
