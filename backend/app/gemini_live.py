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

from backend.app.gemini import GEMINI_LIVE_MODEL, client, get_live_config
from backend.app.logger import get_logger

logger = get_logger(__name__)


class GeminiLiveSession:
    """
    Manages one Gemini Live session.

    IMPORTANT:
    Only ONE coroutine is allowed to consume session.receive().
    """

    def __init__(
        self,
        session_id: str,
        language: str = "en",
    ):
        self.session_id = session_id
        self.language = language

        self._session_context = None
        self.session = None

        self.connected = False
        self.message_count = 0

        self.logger = logging.getLogger(
            f"GeminiLive-{session_id}"
        )

        # ----------------------------------------------------
        # Receive protection
        # ----------------------------------------------------

        self._receive_task = None

        # ----------------------------------------------------
        # Send protection
        # ----------------------------------------------------

        self._send_lock = asyncio.Lock()

        # ----------------------------------------------------
        # Lifecycle protection
        # ----------------------------------------------------

        self._close_lock = asyncio.Lock()

    # ========================================================
    # CONNECT
    # ========================================================

    async def connect(self) -> bool:
        """
        Establish connection to Gemini Live API.
        """

        try:
            if client is None:
                self.logger.error(
                    "Gemini client is not configured"
                )
                return False

            # Prevent duplicate connection
            if self.connected and self.session:
                self.logger.warning(
                    f"Session {self.session_id} "
                    f"already connected"
                )
                return True

            self.logger.info(
                f"Connecting to Gemini Live "
                f"(language: {self.language})"
            )

            config = get_live_config()

            self._session_context = (
                client.aio.live.connect(
                    model=GEMINI_LIVE_MODEL,
                    config=config,
                )
            )

            self.session = (
                await self._session_context.__aenter__()
            )

            self.connected = True

            self.logger.info(
                "Connected to Gemini Live successfully"
            )

            return True

        except GoogleAPIError as e:
            self.logger.error(
                f"Google API error: {str(e)}"
            )
            return False

        except Exception as e:
            self.logger.exception(
                f"Connection failed: {str(e)}"
            )

            self.session = None
            self._session_context = None
            self.connected = False

            return False

    # ========================================================
    # SEND AUDIO
    # ========================================================

    async def send_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
    ) -> bool:
        """
        Send audio bytes to Gemini Live.
        """

        if not self.connected or not self.session:
            self.logger.error(
                "Session not connected"
            )
            return False

        try:
            # Serialize outgoing messages
            async with self._send_lock:

                await self.session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_bytes,
                        mime_type=mime_type,
                    )
                )

            self.logger.debug(
                f"Sent {len(audio_bytes)} bytes of audio"
            )

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to send audio: {str(e)}"
            )
            return False

    # ========================================================
    # SEND TEXT
    # ========================================================

    async def send_text(
        self,
        text: str,
    ) -> bool:
        """
        Send text to Gemini Live.
        """

        if not self.connected or not self.session:
            self.logger.error(
                "Session not connected"
            )
            return False

        try:
            # Serialize outgoing messages
            async with self._send_lock:

                await self.session.send_realtime_input(
                    text=text
                )

            self.logger.debug(
                f"Sent text: {text[:50]}..."
            )

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to send text: {str(e)}"
            )
            return False

    # ========================================================
    # RECEIVE RESPONSE
    # ========================================================

    async def receive_response(
        self,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Receive streaming responses from Gemini Live.

        IMPORTANT:
        Only one asyncio task may execute
        self.session.receive().
        """

        if not self.connected or not self.session:
            self.logger.error(
                "Session not connected"
            )
            return

        # ----------------------------------------------------
        # Prevent multiple receive() consumers
        # ----------------------------------------------------

        current_task = asyncio.current_task()

        if self._receive_task is not None:

            if self._receive_task != current_task:

                self.logger.warning(
                    f"Receive loop already running "
                    f"for session {self.session_id}"
                )

                yield {
                    "type": "error",
                    "content": (
                        "Receive loop already running "
                        "for this Gemini Live session"
                    ),
                    "done": True,
                }

                return

        # This task now owns receive()
        self._receive_task = current_task

        self.logger.info(
            f"Gemini Live receive loop started: "
            f"{self.session_id}"
        )

        try:

            # ------------------------------------------------
            # ONLY THIS TASK calls session.receive()
            # ------------------------------------------------

            async for response in self.session.receive():

                self.message_count += 1

                # --------------------------------------------
                # Server content
                # --------------------------------------------

                server_content = getattr(
                    response,
                    "server_content",
                    None,
                )

                if not server_content:
                    continue

                # --------------------------------------------
                # Input transcription
                # --------------------------------------------

                input_transcription = getattr(
                    server_content,
                    "input_transcription",
                    None,
                )

                if input_transcription:

                    transcript = getattr(
                        input_transcription,
                        "text",
                        None,
                    )

                    if transcript:

                        yield {
                            "type": "input_transcript",
                            "content": transcript,
                            "done": False,
                        }

                # --------------------------------------------
                # Output transcription
                # --------------------------------------------

                output_transcription = getattr(
                    server_content,
                    "output_transcription",
                    None,
                )

                if output_transcription:

                    transcript = getattr(
                        output_transcription,
                        "text",
                        None,
                    )

                    if transcript:

                        yield {
                            "type": "output_transcript",
                            "content": transcript,
                            "done": False,
                        }

                # --------------------------------------------
                # Model turn
                # --------------------------------------------

                model_turn = getattr(
                    server_content,
                    "model_turn",
                    None,
                )

                if model_turn:

                    parts = getattr(
                        model_turn,
                        "parts",
                        [],
                    )

                    for part in parts:

                        # ------------------------------------
                        # Audio response
                        # ------------------------------------

                        inline_data = getattr(
                            part,
                            "inline_data",
                            None,
                        )

                        if inline_data:

                            yield {
                                "type": "audio",
                                "mime_type": getattr(
                                    inline_data,
                                    "mime_type",
                                    "audio/pcm",
                                ),
                                "content": inline_data.data,
                                "done": False,
                            }

                        # ------------------------------------
                        # Text response
                        # ------------------------------------

                        text = getattr(
                            part,
                            "text",
                            None,
                        )

                        if text:

                            yield {
                                "type": "text",
                                "content": text,
                                "done": False,
                            }

                # --------------------------------------------
                # Turn complete
                # --------------------------------------------

                if getattr(
                    server_content,
                    "turn_complete",
                    False,
                ):

                    yield {
                        "type": "turn_complete",
                        "done": True,
                    }

        except asyncio.CancelledError:

            self.logger.info(
                f"Receive loop cancelled: "
                f"{self.session_id}"
            )

            raise

        except Exception as e:

            error_message = str(e)

            # --------------------------------------------
            # Normal WebSocket close
            # --------------------------------------------

            if "1000" in error_message:

                self.logger.info(
                    f"Gemini Live connection closed "
                    f"normally: {self.session_id}"
                )

                return

            # --------------------------------------------
            # Actual error
            # --------------------------------------------

            self.logger.exception(
                f"Error receiving response: "
                f"{error_message}"
            )

            yield {
                "type": "error",
                "content": error_message,
                "done": True,
            }

        finally:

            # Only clear if THIS task owns the receiver
            if self._receive_task == current_task:

                self._receive_task = None

            self.logger.info(
                f"Gemini Live receive loop ended: "
                f"{self.session_id}"
            )

    # ========================================================
    # CLOSE
    # ========================================================

    async def close(self) -> None:
        """
        Close Gemini Live session safely.
        """

        async with self._close_lock:

            self.logger.info(
                f"Closing Gemini Live session: "
                f"{self.session_id}"
            )

            # ------------------------------------------------
            # Stop receive task
            # ------------------------------------------------

            current_task = asyncio.current_task()

            if (
                self._receive_task
                and self._receive_task != current_task
                and not self._receive_task.done()
            ):

                self.logger.info(
                    f"Cancelling receive task: "
                    f"{self.session_id}"
                )

                self._receive_task.cancel()

                try:
                    await self._receive_task

                except asyncio.CancelledError:
                    pass

                except Exception:
                    pass

            self._receive_task = None

            # ------------------------------------------------
            # Close Gemini connection
            # ------------------------------------------------

            try:

                if self._session_context:

                    await self._session_context.__aexit__(
                        None,
                        None,
                        None,
                    )

            except Exception as e:

                self.logger.warning(
                    f"Error closing Gemini connection: "
                    f"{str(e)}"
                )

            finally:

                self.session = None
                self._session_context = None
                self.connected = False

                self.logger.info(
                    f"Session closed: "
                    f"{self.session_id}"
                )
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
