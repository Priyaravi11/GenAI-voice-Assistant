"""
WebSocket Handler
File: backend/app/websocket.py

Receives the user's query (already transcribed to English text, per the
confirmed workflow: user speaks -> Gemini understands -> returns as
English) over a WebSocket connection, routes it through the orchestrator
(Supervisor -> Agent -> RAG/Tool -> Escalation), and sends the response
back to the client.

------------------------------------------------------------------------
STUBBED DEPENDENCIES — swap these out once the real files exist:
    1. SessionContext / get_or_create_context()  -> replace with the
       real backend/app/context.py once built (session state: customer_id,
       language, conversation_id, history — NOT rag/context/context_builder.py,
       which is a different, RAG-only file).
    2. process_query()                            -> replace with the real
       backend/app/orchestrator.py once built (Supervisor routing +
       agent RAG/Tool pipeline).
Both are marked "# INTEGRATION POINT" below. Everything else (the
WebSocket connection handling, escalation check, message format) is
real, working logic — not a stub.
------------------------------------------------------------------------

Assumes this file is mounted onto an existing FastAPI app in main.py, e.g.:

    from app.websocket import router as websocket_router
    app.include_router(websocket_router)
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from escalation import EscalationManager

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------
# STUB 1 — Session Context
# INTEGRATION POINT: replace with the real backend/app/context.py
# once it exists. Field names below match what's documented in the
# architecture doc (customer_id, language, conversation_id, history).
# ------------------------------------------------------------------

@dataclass
class SessionContext:
    conversation_id: str
    customer_id: Optional[str] = None
    language: str = "English"
    history: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "language": self.language,
            "history": self.history,
        }


def get_or_create_context(customer_id: Optional[str] = None, language: str = "English") -> SessionContext:
    """
    STUB — creates a fresh in-memory context per connection.
    Real context.py will likely persist this (e.g. per customer/session
    store) rather than recreate it each time. Swap this function out,
    keep the SessionContext shape if it matches the real one.
    """
    return SessionContext(
        conversation_id=str(uuid.uuid4()),
        customer_id=customer_id,
        language=language,
    )


# ------------------------------------------------------------------
# STUB 2 — Orchestrator
# INTEGRATION POINT: replace with the real backend/app/orchestrator.py
# once it exists. Expected return shape matches what escalation.py and
# every agent's handle() already produce:
#   {"agent": ..., "intent": ..., "escalate": bool, "response": str, ...}
# ------------------------------------------------------------------

async def process_query(english_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    STUB — echoes the query back instead of real Supervisor -> Agent ->
    RAG/Tool routing. Replace with a call to the real orchestrator, e.g.:

        from orchestrator import QueryOrchestrator
        result = await orchestrator.process_query(english_query, context)
        return result
    """
    logger.warning("Using STUB process_query — real orchestrator.py not wired in yet.")
    return {
        "agent": "stub",
        "intent": "stub_echo",
        "escalate": False,
        "response": f"(stub response) You said: {english_query}",
        "language": context.get("language", "English"),
    }


# ------------------------------------------------------------------
# WebSocket endpoint — real logic, not stubbed
# ------------------------------------------------------------------

@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    Expected incoming message (JSON):
        {
            "query": "why is my bill so high",
            "customer_id": "CUST123",       // optional
            "language": "Tamil"              // optional, defaults to English
        }

    Outgoing message (JSON):
        {
            "response": "...",
            "escalated": false,
            "language": "Tamil"
        }
    """
    await websocket.accept()
    escalation_manager = EscalationManager()
    context: Optional[SessionContext] = None

    logger.info("WebSocket connection opened.")

    try:
        while True:
            data = await websocket.receive_json()

            query = data.get("query", "").strip()
            if not query:
                await websocket.send_json({"error": "Empty query received."})
                continue

            # Create context on first message, reuse for the rest of the session
            if context is None:
                context = get_or_create_context(
                    customer_id=data.get("customer_id"),
                    language=data.get("language", "English"),
                )
            elif "language" in data:
                # Allow language to be updated mid-conversation if the
                # client sends it again (e.g. user switches language)
                context.language = data["language"]

            # --- Step 1: route through orchestrator (STUB for now) ---
            agent_result = await process_query(query, context.as_dict())

            # --- Step 2: check escalation ---
            if escalation_manager.should_escalate(agent_result):
                final = escalation_manager.handle_escalation(
                    reason=agent_result.get("intent", "unspecified"),
                    context=context.as_dict(),
                )
            else:
                final = agent_result

            # --- Step 3: update history, send response ---
            context.history.append({"query": query, "response": final.get("response")})

            await websocket.send_json({
                "response": final.get("response"),
                "escalated": final.get("escalate", final.get("escalated", False)),
                "language": final.get("language", context.language),
            })

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected. conversation_id=%s",
            context.conversation_id if context else "unknown",
        )
    except Exception:
        logger.exception("Unexpected error in voice_websocket.")
        await websocket.close(code=1011)