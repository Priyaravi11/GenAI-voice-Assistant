"""
Main Application Entry Point
File: backend/app/main.py

FastAPI application initialization and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api.routes import analytics
from backend.app.api.routes import calls
from backend.app.api.routes import rag
from backend.app.api.routes import session
from backend.app.api.routes import tools
from backend.app.websocket import router as websocket_router


# ============================================================
# Initialize FastAPI App
# ============================================================

app = FastAPI(
    title="Multilingual GenAI Voice Assistant",
    description="Telecom customer-care backend with RAG and multi-agent support",
    version="1.0.0",
)


# ============================================================
# CORS Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API Routes
# ============================================================

app.include_router(session.router)
app.include_router(calls.router)
app.include_router(analytics.router)
app.include_router(rag.router)
app.include_router(tools.router)


# ============================================================
# WebSocket Routes
# ============================================================

app.include_router(websocket_router)


# ============================================================
# Health Endpoints
# ============================================================

@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        {"status": "healthy", "version": "1.0.0"}
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app": settings.APP_NAME,
    }


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns basic API information.
    """
    return {
        "success": True,
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "description": "Multilingual GenAI Voice Assistant for Telecom Customer Care",
        "endpoints": {
            "health": "/health",
            "websocket": "ws://localhost:8000/ws/voice/{session_id}",
            "api_docs": "/docs",
            "openapi_schema": "/openapi.json",
        },
    }


# ============================================================
# Startup/Shutdown Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    print("=" * 60)
    print(f"Starting {settings.APP_NAME}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"CORS Origins: http://localhost:5173, http://localhost:3000")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("=" * 60)
    print(f"Shutting down {settings.APP_NAME}")
    print("=" * 60)
