"""
Gemini Live Audio Handler
File: backend/app/gemini_live.py

Manages real-time bidirectional audio streaming with Gemini Live API.

Responsibilities:
1. Establish Gemini Live sessions
2. Stream audio input to Gemini
3. Receive audio/text responses
4. Manage session lifecycle
5. Handle audio transcription
6. Error recovery and reconnection
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, Optional
import json

from google.genai import types

try:
    from google.api_core.exceptions import GoogleAPIError
except ImportError:
    GoogleAPIError = Exception

from backend.app.gemini import client, get_live_config
from backend.app.logger import get_logger

logger = get_logger(__name__)


class GeminiLiveSession:
    """
    Manages a single Gemini Live audio session.
    
    Handles:
    - Session lifecycle (connect, send, receive, close)
    - Audio encoding/decoding
    - Message serialization
    - Error handling and reconnection
    """

    def __init__(self, session_id: str, language: str = "en"):
        """
        Initialize a Gemini Live session.
        
        Args:
            session_id: Unique session identifier
            language: Language code (en, es, fr, etc.)
        """
        self.session_id = session_id
        self.language = language
        self.session = None
        self.connected = False
        self.message_count = 0
        self.logger = logging.getLogger(f"GeminiLive-{session_id}")

    async def connect(self) -> bool:
        """
        Establish connection to Gemini Live API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if client is None:
                self.logger.error("Gemini client is not configured")
                return False

            self.logger.info(f"Connecting to Gemini Live (language: {self.language})")
            
            config = get_live_config()
            self.session = await client.aio.live.connect(
                model="gemini-23.6-flash",
                config=config,
            )
            
            self.connected = True
            self.logger.info("Connected to Gemini Live successfully")
            return True

        except GoogleAPIError as e:
            self.logger.error(f"Google API error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    async def send_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> bool:
        """
        Send audio bytes to Gemini Live.
        
        Args:
            audio_bytes: Raw audio data
            mime_type: Audio format (audio/wav, audio/mp3, audio/ogg, etc.)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.session:
            self.logger.error("Session not connected")
            return False

        try:
            # Create audio part
            audio_part = types.Part(
                inline_data=types.Blob(
                    mime_type=mime_type,
                    data=audio_bytes,
                )
            )

            # Send as content
            content = types.Content(parts=[audio_part])
            await self.session.send(content)

            self.logger.debug(f"Sent {len(audio_bytes)} bytes of audio")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send audio: {str(e)}")
            return False

    async def send_text(self, text: str) -> bool:
        """
        Send text to Gemini Live (fallback if audio unavailable).
        
        Args:
            text: Text message
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.session:
            self.logger.error("Session not connected")
            return False

        try:
            text_part = types.Part(text=text)
            content = types.Content(parts=[text_part])
            await self.session.send(content)

            self.logger.debug(f"Sent text: {text[:50]}...")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send text: {str(e)}")
            return False

    async def receive_response(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Receive streaming responses from Gemini Live.
        
        Yields:
            Dict with keys:
            - type: 'audio' or 'text'
            - content: audio bytes or text string
            - transcript: text transcript if available
            - done: True if response complete
        """
        if not self.connected or not self.session:
            self.logger.error("Session not connected")
            return

        try:
            async for response in self.session.receive():
                self.message_count += 1

                # Handle server content (response from Gemini)
                if response.server_content:
                    for part in response.server_content.parts:
                        # Audio response
                        if part.inline_data:
                            yield {
                                "type": "audio",
                                "mime_type": part.inline_data.mime_type,
                                "content": part.inline_data.data,
                                "done": False,
                            }

                        # Text response
                        elif part.text:
                            yield {
                                "type": "text",
                                "content": part.text,
                                "done": False,
                            }

                # Handle turns to see when response is complete
                if response.turns:
                    for turn in response.turns:
                        if turn.role == "model":
                            yield {
                                "type": "turn_complete",
                                "done": True,
                            }

        except asyncio.CancelledError:
            self.logger.info("Session receive cancelled")
        except Exception as e:
            self.logger.error(f"Error receiving response: {str(e)}")
            yield {
                "type": "error",
                "content": str(e),
                "done": True,
            }

    async def close(self) -> None:
        """
        Close Gemini Live session.
        """
        try:
            if self.session:
                await self.session.close()
            self.connected = False
            self.logger.info("Session closed")
        except Exception as e:
            self.logger.error(f"Error closing session: {str(e)}")


# ============================================================
# Global Session Manager
# ============================================================

_live_sessions: Dict[str, GeminiLiveSession] = {}
_lock = asyncio.Lock()


async def create_live_session(
    session_id: str,
    language: str = "en",
) -> Optional[GeminiLiveSession]:
    """
    Create and connect a new Gemini Live session.
    
    Args:
        session_id: Unique identifier
        language: Language code
        
    Returns:
        GeminiLiveSession if successful, None otherwise
    """
    async with _lock:
        if session_id in _live_sessions:
            logger.warning(f"Session {session_id} already exists")
            return _live_sessions[session_id]

        session = GeminiLiveSession(session_id, language)
        
        if await session.connect():
            _live_sessions[session_id] = session
            return session
        else:
            return None


async def get_live_session(session_id: str) -> Optional[GeminiLiveSession]:
    """
    Get existing Gemini Live session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        GeminiLiveSession if exists, None otherwise
    """
    return _live_sessions.get(session_id)


async def close_live_session(session_id: str) -> None:
    """
    Close and remove a Gemini Live session.
    
    Args:
        session_id: Session identifier
    """
    async with _lock:
        session = _live_sessions.get(session_id)
        if session:
            await session.close()
            del _live_sessions[session_id]
            logger.info(f"Session {session_id} closed and removed")


async def list_live_sessions() -> list:
    """
    Get list of active session IDs.
    
    Returns:
        List of session IDs
    """
    return list(_live_sessions.keys())
