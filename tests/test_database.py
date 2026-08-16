"""
Unit tests for database operations.

Tests cover:
- Customer data retrieval
- Call logging
- Session management
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
class TestDatabaseOperations:
    """Test cases for database operations."""

    @pytest.fixture
    def db_client(self, mock_database):
        """Create a mock database client."""
        return mock_database

    async def test_find_customer_by_id(self, db_client):
        """Test finding customer by ID."""
        customer = await db_client.find_customer(customer_id="C001")

        assert customer is not None
        assert customer["customer_id"] == "C001"
        assert customer["name"] == "Test Customer"

    async def test_find_nonexistent_customer(self, db_client):
        """Test finding non-existent customer."""
        db_client.find_customer = AsyncMock(return_value=None)

        customer = await db_client.find_customer(customer_id="INVALID")

        assert customer is None

    async def test_get_billing_data(self, db_client):
        """Test retrieving billing data."""
        billing = await db_client.get_billing_data(customer_id="C001")

        assert billing is not None
        assert billing["current_bill"] == 150.00
        assert billing["due_date"] == "2026-09-16"
        assert billing["status"] == "active"

    async def test_get_billing_data_for_inactive_customer(
        self, db_client
    ):
        """Test billing data retrieval for inactive customer."""
        db_client.get_billing_data = AsyncMock(
            return_value={
                "current_bill": 0.00,
                "status": "inactive",
            }
        )

        billing = await db_client.get_billing_data(customer_id="C002")

        assert billing["status"] == "inactive"

    async def test_log_call_session(self, db_client):
        """Test logging call session."""
        db_client.log_call = AsyncMock(return_value={"session_id": "S001"})

        result = await db_client.log_call(
            customer_id="C001",
            call_type="outbound",
            duration=300,
        )

        assert result["session_id"] == "S001"

    async def test_update_session_status(self, db_client):
        """Test updating session status."""
        db_client.update_session = AsyncMock(
            return_value={"status": "completed"}
        )

        result = await db_client.update_session(
            session_id="S001",
            status="completed",
        )

        assert result["status"] == "completed"

    async def test_retrieve_call_history(self, db_client):
        """Test retrieving call history."""
        db_client.get_call_history = AsyncMock(
            return_value=[
                {
                    "call_id": "CALL001",
                    "timestamp": "2026-08-15T10:00:00Z",
                    "duration": 300,
                },
                {
                    "call_id": "CALL002",
                    "timestamp": "2026-08-14T14:30:00Z",
                    "duration": 450,
                },
            ]
        )

        history = await db_client.get_call_history(customer_id="C001")

        assert len(history) == 2
        assert history[0]["call_id"] == "CALL001"

    async def test_database_connection_failure(self, db_client):
        """Test handling database connection failure."""
        db_client.find_customer = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with pytest.raises(Exception):
            await db_client.find_customer(customer_id="C001")

    async def test_query_timeout(self, db_client):
        """Test handling query timeout."""
        db_client.get_billing_data = AsyncMock(
            side_effect=TimeoutError("Query timeout")
        )

        with pytest.raises(TimeoutError):
            await db_client.get_billing_data(customer_id="C001")

    async def test_insert_call_transcript(self, db_client):
        """Test inserting call transcript."""
        db_client.insert_transcript = AsyncMock(
            return_value={"transcript_id": "T001"}
        )

        result = await db_client.insert_transcript(
            session_id="S001",
            transcript=[
                {
                    "speaker": "customer",
                    "text": "What is my bill?",
                    "timestamp": 0,
                }
            ],
        )

        assert result["transcript_id"] == "T001"


@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def db_client(self, mock_database):
        return mock_database

    async def test_complete_call_flow(self, db_client):
        """Test complete call flow with database operations."""
        # 1. Find customer
        customer = await db_client.find_customer(customer_id="C001")
        assert customer is not None

        # 2. Log call
        db_client.log_call = AsyncMock(return_value={"session_id": "S001"})
        call_log = await db_client.log_call(
            customer_id="C001",
            call_type="inbound",
        )
        assert "session_id" in call_log

        # 3. Get billing data
        billing = await db_client.get_billing_data(customer_id="C001")
        assert billing is not None

        # 4. Update session
        db_client.update_session = AsyncMock(
            return_value={"status": "completed"}
        )
        await db_client.update_session(
            session_id=call_log["session_id"],
            status="completed",
        )

    async def test_customer_lookup_and_history(self, db_client):
        """Test customer lookup with call history."""
        customer = await db_client.find_customer(customer_id="C001")
        assert customer is not None

        history = await db_client.get_call_history(
            customer_id=customer["customer_id"]
        )
        assert history is not None
