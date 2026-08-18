"""
WebSocket Handler
File: backend/app/websocket.py

Coordinates real-time bidirectional communication between the frontend and
the backend orchestrator.

Supports TWO modes:
1. TEXT MODE - Traditional text queries (used for now)
2. AUDIO MODE - Real-time audio streaming with Gemini Live (available)

Responsibilities:
1. Accept WebSocket connections
2. Receive client messages (text queries, audio streams, control events)
3. Forward requests to the orchestrator or Gemini Live
4. Return structured events (responses, sources, status, audio)
5. Handle disconnects and errors gracefully
6. Maintain session context
7. Support multi-turn conversation
8. Stream audio in real-time

Message Format (Client → Server):

TEXT MODE:
{
    "type": "user_message" | "start_call" | "end_call" | "get_status",
    "session_id": "...",
    "customer_id": "...",
    "language": "en",
    "content": "..."  # for user_message
}

AUDIO MODE:
{
    "type": "audio_chunk" | "audio_start" | "audio_end",
    "session_id": "...",
    "data": "base64_encoded_audio_bytes",
    "mime_type": "audio/wav"
}

Response Format (Server → Client):
{
    "type": "assistant_response" | "rag_source" | "tool_execution" | 
            "escalation" | "error" | "audio_response" | "audio_transcript",
    "session_id": "...",
    "content": "...",
    "confidence": 0.95,
    "intent": "...",
    ...
}
"""

import json
import logging
from typing import Any, Dict, Optional
import uuid
import base64
import asyncio

from fastapi import APIRouter, WebSocketException, status
from fastapi.websockets import WebSocket

from backend.app.context import get_or_create_session, remove_session
from backend.app.orchestrator import orchestrator
from backend.app.validation import validate_session_id, validate_language
from backend.app.logger import get_logger
from backend.app.gemini_live import (
    create_live_session,
    get_live_session,
    close_live_session,
)

logger = get_logger(__name__)

# ============================================================
# Router Setup
# ============================================================

router = APIRouter()

# ============================================================
# WebSocket Connection Manager
# ============================================================

class ConnectionManager:
    """
    Manages WebSocket connections and session lifecycle.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_contexts: Dict[str, Any] = {}

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        """Connect a new WebSocket session."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        """Disconnect a WebSocket session."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")

    async def send_personal(
        self,
        session_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {str(e)}")

    def is_connected(self, session_id: str) -> bool:
        """Check if a session is connected."""
        return session_id in self.active_connections


manager = ConnectionManager()


# ============================================================
# WebSocket Endpoint
# ============================================================

@router.websocket("/ws/voice/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for voice assistant communication.

    Accepts connections at: ws://localhost:8000/ws/voice/{session_id}

    Example client code:

        const ws = new WebSocket("ws://localhost:8000/ws/voice/my-session-123");

        ws.onopen = () => {
            ws.send(JSON.stringify({
                "type": "user_message",
                "content": "What plans do you offer?",
                "language": "en"
            }));
        };

        ws.onmessage = (event) => {
            const response = JSON.parse(event.data);
            console.log(response);
        };
    """

    # ========================================================
    # SETUP
    # ========================================================

    try:
        # Validate session ID
        session_id = validate_session_id(session_id)
    except ValueError as e:
        logger.error(f"Invalid session ID: {str(e)}")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid session ID",
        )
        return

    try:
        # Accept the connection
        await manager.connect(session_id, websocket)

        # Get or create session context
        context = get_or_create_session(
            session_id=session_id,
            language="en",
        )
        manager.session_contexts[session_id] = context

        # Send connection confirmation
        await manager.send_personal(
            session_id,
            {
                "type": "connection_established",
                "session_id": session_id,
                "message": "Connected to GenAI Voice Assistant",
            },
        )

    except Exception as e:
        logger.error(f"Connection setup failed: {str(e)}")
        await websocket.close(
            code=status.WS_1011_SERVER_ERROR,
            reason="Connection setup failed",
        )
        return

    # ========================================================
    # MESSAGE LOOP
    # ========================================================

    try:
        while True:
            # ====================================================
            # RECEIVE MESSAGE FROM CLIENT
            # ====================================================

            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                await manager.send_personal(
                    session_id,
                    {
                        "type": "error",
                        "error": "Invalid JSON format",
                    },
                )
                continue
            except Exception as e:
                logger.error(f"Failed to receive message: {str(e)}")
                break

            # ====================================================
            # VALIDATE MESSAGE
            # ====================================================

            message_type = data.get("type", "user_message")
            content = data.get("content", "").strip()
            language = data.get("language", "en").lower()
            customer_id = data.get("customer_id")

            # Validate language
            try:
                language = validate_language(language)
            except ValueError as e:
                await manager.send_personal(
                    session_id,
                    {
                        "type": "error",
                        "error": str(e),
                    },
                )
                continue

            # ====================================================
            # HANDLE MESSAGE TYPES
            # ====================================================

            if message_type == "user_message":
                await _handle_user_message(
                    session_id=session_id,
                    content=content,
                    language=language,
                    customer_id=customer_id,
                )

            elif message_type == "start_call":
                await _handle_start_call(
                    session_id=session_id,
                    language=language,
                    customer_id=customer_id,
                )

            elif message_type == "end_call":
                await _handle_end_call(session_id=session_id)

            elif message_type == "get_status":
                await _handle_get_status(session_id=session_id)

            # ====================================================
            # AUDIO STREAMING HANDLERS
            # ====================================================

            elif message_type == "audio_start":
                await _handle_audio_start(
                    session_id=session_id,
                    language=language,
                    customer_id=customer_id,
                )

            elif message_type == "audio_chunk":
                audio_data = data.get("data", "")
                mime_type = data.get("mime_type", "audio/wav")
                await _handle_audio_chunk(
                    session_id=session_id,
                    audio_data=audio_data,
                    mime_type=mime_type,
                )

            elif message_type == "audio_end":
                await _handle_audio_end(session_id=session_id)

            else:
                await manager.send_personal(
                    session_id,
                    {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                    },
                )

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

    finally:
        # ========================================================
        # CLEANUP
        # ========================================================

        manager.disconnect(session_id)
        remove_session(session_id)
        logger.info(f"Session closed: {session_id}")


# ============================================================
# MESSAGE HANDLERS
# ============================================================

async def _handle_user_message(
    session_id: str,
    content: str,
    language: str,
    customer_id: Optional[str],
) -> None:
    """
    Handle a user message query.

    Flow:
    1. Validate input
    2. Send to orchestrator
    3. Stream response back to client
    """

    # Validate content
    if not content:
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": "Message content cannot be empty",
            },
        )
        return

    if len(content) > 5000:
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": "Message is too long (max 5000 chars)",
            },
        )
        return

    logger.info(
        f"Processing user message: {session_id} | {language} | {len(content)} chars"
    )

    try:
        # Send "thinking" status
        await manager.send_personal(
            session_id,
            {
                "type": "status",
                "status": "processing",
                "message": "Analyzing your query...",
            },
        )

        # Process through orchestrator
        result = await orchestrator.process_text(
            session_id=session_id,
            customer_query=content,
            language=language,
            customer_id=customer_id,
        )

        # Extract response components
        response = result.get("response", "")
        confidence = result.get("confidence", 0.0)
        intent = result.get("intent", "general")
        rag_context = result.get("rag_context", {})
        escalated = result.get("escalated", False)
        requires_customer_id = result.get(
            "requires_customer_id",
            False,
        )

        # Send response
        await manager.send_personal(
            session_id,
            {
                "type": "assistant_response",
                "content": response,
                "language": language,
                "confidence": confidence,
                "intent": intent,
                "escalated": escalated,
                "requires_customer_id": requires_customer_id,
            },
        )

        # Send RAG sources if available
        if rag_context and rag_context.get("retrieved_context"):
            sources = [
                {
                    "source": doc.get("source", "Unknown"),
                    "relevance": doc.get("relevance", 0.0),
                }
                for doc in rag_context.get("retrieved_context", [])
            ]
            await manager.send_personal(
                session_id,
                {
                    "type": "rag_sources",
                    "sources": sources,
                },
            )

        # Send escalation notice if applicable
        if escalated:
            await manager.send_personal(
                session_id,
                {
                    "type": "escalation_notice",
                    "reason": result.get("escalation_reason", "Escalated to human agent"),
                    "confidence": confidence,
                },
            )

        logger.info(
            f"User message processed successfully: {session_id} | "
            f"confidence: {confidence} | escalated: {escalated}"
        )

    except Exception as e:
        logger.error(f"Error processing user message: {str(e)}", exc_info=True)
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": "Failed to process your message. Please try again.",
                "details": str(e),
            },
        )


async def _handle_start_call(
    session_id: str,
    language: str,
    customer_id: Optional[str],
) -> None:
    """
    Handle call start event.

    Used to initialize a new call session.
    """

    logger.info(f"Call started: {session_id} | {language}")

    context = manager.session_contexts.get(session_id)
    if context:
        context.update(
            language=language,
            customer_id=customer_id,
        )

    await manager.send_personal(
        session_id,
        {
            "type": "call_started",
            "session_id": session_id,
            "language": language,
            "message": f"Call initiated. Listening in {language}.",
        },
    )


async def _handle_end_call(session_id: str) -> None:
    """
    Handle call end event.

    Gracefully closes the session.
    """

    logger.info(f"Call ended: {session_id}")

    context = manager.session_contexts.get(session_id)
    if context:
        context.close()

    await manager.send_personal(
        session_id,
        {
            "type": "call_ended",
            "session_id": session_id,
            "message": "Call ended. Thank you for using GenAI Voice Assistant.",
        },
    )

    # Close the connection
    ws = manager.active_connections.get(session_id)
    if ws:
        await ws.close()


async def _handle_get_status(session_id: str) -> None:
    """
    Handle status request.

    Returns current session status and context.
    """

    context = manager.session_contexts.get(session_id)

    status_data = {
        "type": "status_response",
        "session_id": session_id,
        "connected": manager.is_connected(session_id),
        "language": context.language if context else "unknown",
        "customer_id": context.customer_id if context else None,
        "message_count": len(context.messages) if context else 0,
    }

    await manager.send_personal(
        session_id,
        status_data,
    )


# ============================================================
# AUDIO STREAMING HANDLERS (Gemini Live)
# ============================================================

async def _handle_audio_start(
    session_id: str,
    language: str,
    customer_id: Optional[str],
) -> None:
    """
    Handle audio stream start.

    Initializes Gemini Live session for real-time audio streaming.
    """

    logger.info(f"Audio stream started: {session_id} | {language}")

    try:
        # Create Gemini Live session
        live_session = await create_live_session(session_id, language)

        if not live_session:
            await manager.send_personal(
                session_id,
                {
                    "type": "error",
                    "error": "Failed to initialize Gemini Live session",
                },
            )
            return

        # Send confirmation
        await manager.send_personal(
            session_id,
            {
                "type": "audio_stream_ready",
                "session_id": session_id,
                "message": "Audio stream ready. Listening...",
            },
        )

        # Start receiving responses in background
        asyncio.create_task(
            _audio_response_handler(session_id)
        )

    except Exception as e:
        logger.error(f"Error starting audio stream: {str(e)}")
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": f"Failed to start audio stream: {str(e)}",
            },
        )


async def _handle_audio_chunk(
    session_id: str,
    audio_data: str,
    mime_type: str = "audio/wav",
) -> None:
    """
    Handle incoming audio chunk.

    Routes audio to Gemini Live session.
    """

    try:
        # Get Gemini Live session
        live_session = await get_live_session(session_id)

        if not live_session:
            await manager.send_personal(
                session_id,
                {
                    "type": "error",
                    "error": "Audio stream not initialized",
                },
            )
            return

        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            logger.error(f"Failed to decode audio: {str(e)}")
            await manager.send_personal(
                session_id,
                {
                    "type": "error",
                    "error": f"Invalid audio encoding: {str(e)}",
                },
            )
            return

        # Send to Gemini Live
        success = await live_session.send_audio(audio_bytes, mime_type)

        if not success:
            await manager.send_personal(
                session_id,
                {
                    "type": "error",
                    "error": "Failed to send audio to Gemini Live",
                },
            )

    except Exception as e:
        logger.error(f"Error handling audio chunk: {str(e)}")
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": f"Audio processing error: {str(e)}",
            },
        )


async def _handle_audio_end(session_id: str) -> None:
    """
    Handle audio stream end.

    Closes Gemini Live session gracefully.
    """

    logger.info(f"Audio stream ended: {session_id}")

    try:
        await close_live_session(session_id)

        await manager.send_personal(
            session_id,
            {
                "type": "audio_stream_closed",
                "session_id": session_id,
                "message": "Audio stream closed",
            },
        )

    except Exception as e:
        logger.error(f"Error ending audio stream: {str(e)}")


async def _audio_response_handler(session_id: str) -> None:
    """
    Background task to receive and forward Gemini Live responses.

    Runs continuously while audio stream is active.
    """

    try:
        live_session = await get_live_session(session_id)

        if not live_session:
            logger.error(f"Live session not found: {session_id}")
            return

        async for response in live_session.receive_response():
            if not manager.is_connected(session_id):
                logger.info(f"Client disconnected: {session_id}")
                break

            response_type = response.get("type", "unknown")

            if response_type == "audio":
                # Encode audio to base64 for transmission
                audio_b64 = base64.b64encode(response["content"]).decode()

                await manager.send_personal(
                    session_id,
                    {
                        "type": "audio_response",
                        "data": audio_b64,
                        "mime_type": response.get("mime_type", "audio/wav"),
                    },
                )

            elif response_type == "text":
                await manager.send_personal(
                    session_id,
                    {
                        "type": "audio_transcript",
                        "content": response["content"],
                    },
                )

            elif response_type == "turn_complete":
                await manager.send_personal(
                    session_id,
                    {
                        "type": "turn_complete",
                        "message": "Waiting for user input...",
                    },
                )

            elif response_type == "error":
                await manager.send_personal(
                    session_id,
                    {
                        "type": "error",
                        "error": response["content"],
                    },
                )

    except asyncio.CancelledError:
        logger.info(f"Audio response handler cancelled: {session_id}")
    except Exception as e:
        logger.error(f"Error in audio response handler: {str(e)}")
        await manager.send_personal(
            session_id,
            {
                "type": "error",
                "error": f"Audio stream error: {str(e)}",
            },
        )


# ============================================================
# LEGACY ENDPOINT (for compatibility)
# ============================================================

@router.websocket("/ws/{session_id}")
async def websocket_legacy(
    websocket: WebSocket,
    session_id: str,
):
    """
    Legacy WebSocket endpoint for backward compatibility.

    Redirects to the voice endpoint.
    """
    await websocket_endpoint(websocket, session_id)
