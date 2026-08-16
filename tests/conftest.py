"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_gemini():
    """Mock Gemini API client."""
    mock = AsyncMock()
    mock.generate = AsyncMock(
        return_value={
            "response": "Test response",
            "confidence": 0.95,
        }
    )
    return mock


@pytest.fixture
def mock_rag():
    """Mock RAG service."""
    mock = AsyncMock()
    mock.retrieve = AsyncMock(
        return_value=[
            {
                "content": "Test knowledge base content",
                "score": 0.92,
                "source": "test_doc",
            }
        ]
    )
    return mock


@pytest.fixture
def mock_database():
    """Mock database client."""
    mock = AsyncMock()
    mock.find_customer = AsyncMock(
        return_value={
            "customer_id": "C001",
            "name": "Test Customer",
            "phone": "5551234567",
        }
    )
    mock.get_billing_data = AsyncMock(
        return_value={
            "current_bill": 150.00,
            "due_date": "2026-09-16",
            "status": "active",
        }
    )
    return mock


@pytest.fixture
def mock_billing_tool():
    """Mock billing tool."""
    mock = AsyncMock()
    mock.get_bill = AsyncMock(
        return_value={
            "bill_amount": 150.00,
            "due_date": "2026-09-16",
            "charges": [
                {
                    "description": "Monthly Service",
                    "amount": 99.99,
                }
            ],
        }
    )
    return mock


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return MagicMock()


@pytest.fixture
def sample_context():
    """Sample context data for testing."""
    return {
        "customer_id": "C001",
        "session_id": "S001",
        "language": "en",
        "timezone": "UTC",
    }


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is my current bill?"
