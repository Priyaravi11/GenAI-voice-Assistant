import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.context import get_or_create_session
from app.escalation import EscalationManager
from app.orchestrator import orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

escalation_manager = EscalationManager()


@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time customer interaction.

    Client sends:
    {
        "query": "Why is my bill so high?",
        "language": "English",
        "customer_id": "CUST123"
    }

    Server sends:
    {
        "response": "...",
        "escalated": false,
        "language": "English"
    }
    """

    await websocket.accept()

    logger.info(
        "WebSocket connection opened. session_id=%s",
        session_id,
    )

    try:
        while True:

            # Receive message from frontend
            data: Dict[str, Any] = await websocket.receive_json()

            query = str(data.get("query", "")).strip()

            if not query:
                await websocket.send_json(
                    {
                        "error": "Empty query received."
                    }
                )
                continue

            language = data.get(
                "language",
                "en",
            )

            customer_id = data.get("customer_id")

            # Get existing session or create one
            context = get_or_create_session(
                session_id=session_id,
                customer_id=customer_id,
                language=language,
            )

            # Allow language/customer ID updates
            if customer_id:
                context.customer_id = customer_id

            if language:
                context.language = language

            # Process request through orchestrator
            result = await orchestrator.process_text(
                session_id=session_id,
                customer_query=query,
                language=language,
                customer_id=customer_id,
            )

            # Check escalation
            if escalation_manager.should_escalate(result):

                final_result = escalation_manager.handle_escalation(
                    reason=result.get(
                        "intent",
                        "unspecified",
                    ),
                    context={
                        "session_id": session_id,
                        "customer_id": context.customer_id,
                        "language": context.language,
                        "history": context.get_history(),
                    },
                )

            else:
                final_result = result

            # Send response to frontend
            await websocket.send_json(
                {
                    "response": final_result.get(
                        "response",
                        "",
                    ),
                    "escalated": final_result.get(
                        "escalated",
                        final_result.get(
                            "escalate",
                            False,
                        ),
                    ),
                    "language": final_result.get(
                        "language",
                        context.language,
                    ),
                    "session_id": session_id,
                }
            )

    except WebSocketDisconnect:

        logger.info(
            "WebSocket disconnected. session_id=%s",
            session_id,
        )

    except Exception:

        logger.exception(
            "Unexpected WebSocket error. session_id=%s",
            session_id,
        )

        try:
            await websocket.close(
                code=1011,
            )
        except Exception:
            pass