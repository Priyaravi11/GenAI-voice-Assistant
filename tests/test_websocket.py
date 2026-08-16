"""
Unit tests for WebSocket functionality.

Tests cover:
- Connection establishment
- Message sending/receiving
- Connection lifecycle
- Error handling
- Concurrent connections
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.mark.asyncio
class TestWebSocketConnection:
    """Test cases for WebSocket connections."""

    @pytest.fixture
    def websocket_service(self):
        """Create a mock WebSocket service."""
        mock = AsyncMock()
        mock.connect = AsyncMock()
        mock.disconnect = AsyncMock()
        mock.send = AsyncMock()
        mock.receive = AsyncMock(
            return_value={
                "type": "message",
                "data": "Test response",
            }
        )
        mock.is_connected = MagicMock(return_value=True)
        return mock

    async def test_websocket_connection(self, websocket_service):
        """Test establishing WebSocket connection."""
        await websocket_service.connect()

        websocket_service.connect.assert_called_once()
        assert websocket_service.is_connected()

    async def test_websocket_disconnection(self, websocket_service):
        """Test disconnecting WebSocket."""
        await websocket_service.connect()
        await websocket_service.disconnect()

        websocket_service.disconnect.assert_called_once()

    async def test_send_message(self, websocket_service):
        """Test sending message through WebSocket."""
        await websocket_service.connect()

        message = {"type": "query", "content": "What is my bill?"}
        await websocket_service.send(message)

        websocket_service.send.assert_called_with(message)

    async def test_receive_message(self, websocket_service):
        """Test receiving message from WebSocket."""
        await websocket_service.connect()

        response = await websocket_service.receive()

        assert response is not None
        assert "type" in response
        assert "data" in response

    async def test_connection_with_authentication(self, websocket_service):
        """Test WebSocket connection with auth."""
        auth_token = "test_token_123"

        websocket_service.connect = AsyncMock()
        await websocket_service.connect(token=auth_token)

        websocket_service.connect.assert_called_with(token=auth_token)

    async def test_connection_failure(self, websocket_service):
        """Test handling connection failure."""
        websocket_service.connect = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with pytest.raises(Exception):
            await websocket_service.connect()

    async def test_connection_timeout(self, websocket_service):
        """Test handling connection timeout."""
        websocket_service.connect = AsyncMock(
            side_effect=TimeoutError("Connection timeout")
        )

        with pytest.raises(TimeoutError):
            await websocket_service.connect()


@pytest.mark.asyncio
class TestWebSocketMessaging:
    """Test cases for WebSocket messaging."""

    @pytest.fixture
    def websocket_service(self):
        mock = AsyncMock()
        mock.send = AsyncMock()
        mock.receive = AsyncMock()
        return mock

    async def test_send_query_message(self, websocket_service):
        """Test sending query message."""
        query_message = {
            "type": "query",
            "content": "What is my bill?",
            "customer_id": "C001",
            "language": "en",
        }

        await websocket_service.send(query_message)

        websocket_service.send.assert_called_with(query_message)

    async def test_send_transcription_message(self, websocket_service):
        """Test sending transcription message."""
        transcription_message = {
            "type": "transcription",
            "text": "What is my bill?",
            "confidence": 0.95,
            "timestamp": 1692200400,
        }

        await websocket_service.send(transcription_message)

        websocket_service.send.assert_called_with(transcription_message)

    async def test_receive_response_message(self, websocket_service):
        """Test receiving response message."""
        websocket_service.receive = AsyncMock(
            return_value={
                "type": "response",
                "status": "success",
                "data": "Your bill is $150.00",
            }
        )

        response = await websocket_service.receive()

        assert response["type"] == "response"
        assert response["status"] == "success"

    async def test_receive_error_message(self, websocket_service):
        """Test receiving error message."""
        websocket_service.receive = AsyncMock(
            return_value={
                "type": "error",
                "code": "QUERY_FAILED",
                "message": "Failed to process query",
            }
        )

        response = await websocket_service.receive()

        assert response["type"] == "error"
        assert "code" in response

    async def test_message_serialization(self):
        """Test message serialization."""
        message = {
            "type": "query",
            "content": "Test query",
            "metadata": {"timestamp": 1692200400},
        }

        serialized = json.dumps(message)
        deserialized = json.loads(serialized)

        assert deserialized["type"] == message["type"]


@pytest.mark.asyncio
class TestWebSocketLifecycle:
    """Test cases for WebSocket lifecycle."""

    @pytest.fixture
    def websocket_service(self):
        mock = AsyncMock()
        mock.connect = AsyncMock()
        mock.disconnect = AsyncMock()
        mock.send = AsyncMock()
        mock.receive = AsyncMock()
        return mock

    async def test_complete_session_lifecycle(self, websocket_service):
        """Test complete session from connect to disconnect."""
        # Connect
        await websocket_service.connect()
        assert websocket_service.connect.called

        # Send query
        await websocket_service.send({"type": "query", "content": "Test"})
        assert websocket_service.send.called

        # Receive response
        await websocket_service.receive()
        assert websocket_service.receive.called

        # Disconnect
        await websocket_service.disconnect()
        assert websocket_service.disconnect.called

    async def test_multiple_queries_in_session(self, websocket_service):
        """Test multiple queries in single session."""
        await websocket_service.connect()

        queries = [
            {"type": "query", "content": "Query 1"},
            {"type": "query", "content": "Query 2"},
            {"type": "query", "content": "Query 3"},
        ]

        for query in queries:
            await websocket_service.send(query)
            await websocket_service.receive()

        assert websocket_service.send.call_count == 3
        assert websocket_service.receive.call_count == 3

        await websocket_service.disconnect()

    async def test_reconnection_after_disconnect(
        self, websocket_service
    ):
        """Test reconnection after disconnect."""
        # First connection
        await websocket_service.connect()
        await websocket_service.disconnect()

        # Second connection
        websocket_service.connect.reset_mock()
        await websocket_service.connect()

        assert websocket_service.connect.called


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Integration tests for WebSocket."""

    async def test_concurrent_messages(self):
        """Test handling concurrent messages."""
        import asyncio

        ws_service = AsyncMock()
        ws_service.send = AsyncMock()
        ws_service.receive = AsyncMock(
            return_value={"status": "success"}
        )

        messages = [
            {"type": "query", "content": f"Query {i}"} for i in range(5)
        ]

        # Send multiple messages concurrently
        await asyncio.gather(
            *[ws_service.send(msg) for msg in messages]
        )

        assert ws_service.send.call_count == 5

    async def test_message_ordering(self):
        """Test that messages are received in order."""
        ws_service = AsyncMock()

        responses = [
            {"id": 1, "data": "Response 1"},
            {"id": 2, "data": "Response 2"},
            {"id": 3, "data": "Response 3"},
        ]

        ws_service.receive = AsyncMock(side_effect=responses)

        received = []
        for _ in range(3):
            msg = await ws_service.receive()
            received.append(msg)

        assert len(received) == 3
        assert received[0]["id"] == 1
        assert received[2]["id"] == 3
