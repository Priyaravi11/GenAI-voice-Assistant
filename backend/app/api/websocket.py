"""
WebSocket Routes
File: backend/app/routes/websocket.py

Connects the WebSocket route from app.websocket
to the application's route structure.
"""

from fastapi import APIRouter

from backend.app.websocket import router as websocket_router


router = APIRouter()

router.include_router(websocket_router)