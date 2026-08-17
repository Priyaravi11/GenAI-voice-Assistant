"""
Test script for websocket.py
File: tests/test_websocket.py

Tests the WebSocket flow end to end using FastAPI's TestClient, which
doesn't need a real running server or real Gemini/orchestrator — it
uses the STUB process_query() currently in websocket.py.

Once the real orchestrator.py replaces the stub, these tests may need
small updates (e.g. if escalation-triggering test cases need a real
query that genuinely has no RAG/Tool match) — but the connection/
message-format tests below will keep working regardless.

Run:
    python -m pytest tests/test_websocket.py -v
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
_BACKEND_APP = os.path.join(_PROJECT_ROOT, "backend", "app")
if _BACKEND_APP not in sys.path:
    sys.path.insert(0, _BACKEND_APP)

from fastapi import FastAPI
from fastapi.testclient import TestClient

from websocket import router as websocket_router

app = FastAPI()
app.include_router(websocket_router)
client = TestClient(app)


def test_basic_query_gets_response():
    with client.websocket_connect("/ws/voice") as ws:
        ws.send_json({"query": "what plans do you have", "language": "English"})
        data = ws.receive_json()
        assert "response" in data
        assert data["language"] == "English"
        assert data["escalated"] is False


def test_empty_query_returns_error():
    with client.websocket_connect("/ws/voice") as ws:
        ws.send_json({"query": "", "language": "English"})
        data = ws.receive_json()
        assert "error" in data


def test_language_defaults_to_english():
    with client.websocket_connect("/ws/voice") as ws:
        ws.send_json({"query": "hello"})  # no language key at all
        data = ws.receive_json()
        assert data["language"] == "English"


def test_tamil_language_is_respected():
    with client.websocket_connect("/ws/voice") as ws:
        ws.send_json({"query": "hello", "language": "Tamil"})
        data = ws.receive_json()
        assert data["language"] == "Tamil"


def test_multi_turn_conversation_keeps_context():
    with client.websocket_connect("/ws/voice") as ws:
        ws.send_json({"query": "first question", "language": "English", "customer_id": "CUST1"})
        first = ws.receive_json()
        assert "response" in first

        ws.send_json({"query": "second question"})
        second = ws.receive_json()
        assert "response" in second
        # language should persist across turns without being resent
        assert second["language"] == "English"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])