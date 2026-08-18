from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import websocket as websocket_module


client = TestClient(app)


async def _fake_process_text(
    session_id: str,
    customer_query: str,
    language: str = "en",
    customer_id: str | None = None,
):
    return {
        "session_id": session_id,
        "customer_id": customer_id,
        "language": language,
        "agent": "general",
        "confidence": 0.91,
        "response": f"Handled: {customer_query}",
        "rag_context": {},
        "escalated": False,
        "requires_customer_id": False,
    }


def test_voice_websocket_user_message(monkeypatch):
    monkeypatch.setattr(
        websocket_module.orchestrator,
        "process_text",
        _fake_process_text,
    )

    with client.websocket_connect("/ws/voice/test-session") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connection_established"
        assert connected["session_id"] == "test-session"

        ws.send_json(
            {
                "type": "user_message",
                "content": "hello",
                "language": "en",
            }
        )

        status = ws.receive_json()
        assert status["type"] == "status"
        assert status["status"] == "processing"

        response = ws.receive_json()
        assert response["type"] == "assistant_response"
        assert response["content"] == "Handled: hello"
        assert response["language"] == "en"
        assert response["confidence"] == 0.91


def test_voice_websocket_rejects_empty_message(monkeypatch):
    monkeypatch.setattr(
        websocket_module.orchestrator,
        "process_text",
        _fake_process_text,
    )

    with client.websocket_connect("/ws/voice/test-session-empty") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "type": "user_message",
                "content": "",
                "language": "en",
            }
        )

        response = ws.receive_json()
        assert response["type"] == "error"
        assert response["error"] == "Message content cannot be empty"

