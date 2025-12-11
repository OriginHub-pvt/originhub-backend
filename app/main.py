from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import api_router
from app.database import engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get CORS origins from environment or use default
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Create FastAPI app
app = FastAPI(
    title="OriginHub API",
    description="Backend API for OriginHub - Idea generation and chat platform",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # allow_headers=["Content-Type", "Authorization"],
    allow_headers=["*"],
)

# Include all API routers (centralized in routes/__init__.py)
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {"success": True, "message": "OriginHub API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    """
    Health check endpoint with database connectivity check.
    Returns detailed status of the API and its dependencies.
    """
    health_status = {
        "success": True,
        "status": "healthy",
        "api": "operational",
        "database": "unknown",
    }

    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"
        health_status["success"] = False  # API is running but DB is down

    return health_status
