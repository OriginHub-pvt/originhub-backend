from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import api_router
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
    allow_origins=cors_origins,
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
    """Health check endpoint"""
    return {"success": True, "status": "healthy"}
