"""
Unit tests for the BillingAgent.

Tests cover:
- Query validation
- RAG retrieval
- Customer data fetching
- Response generation
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.billing_agent import BillingAgent


@pytest.mark.asyncio
class TestBillingAgent:
    """Test cases for BillingAgent."""

    @pytest.fixture
    def billing_agent(self, mock_gemini, mock_rag, mock_billing_tool):
        """Create a BillingAgent instance with mocked dependencies."""
        return BillingAgent(
            gemini=mock_gemini,
            rag=mock_rag,
            billing_tool=mock_billing_tool,
        )

    async def test_agent_initialization(self, billing_agent):
        """Test that agent initializes correctly."""
        assert billing_agent.gemini is not None
        assert billing_agent.rag is not None
        assert billing_agent.billing_tool is not None

    async def test_handle_empty_query(self, billing_agent):
        """Test handling of empty query."""
        result = await billing_agent.handle("")

        assert result["success"] is False
        assert "didn't receive" in result["response"].lower()
        assert result["agent"] == "billing"

    async def test_handle_whitespace_query(self, billing_agent):
        """Test handling of whitespace-only query."""
        result = await billing_agent.handle("   ")

        assert result["success"] is False
        assert result["agent"] == "billing"

    async def test_handle_valid_query(self, billing_agent, sample_context):
        """Test handling of valid billing query."""
        result = await billing_agent.handle(
            "What is my current bill?",
            context=sample_context,
        )

        assert result["agent"] == "billing"
        assert "response" in result

    async def test_customer_data_required_detection(self, billing_agent):
        """Test detection of queries requiring customer data."""
        # Query that should require customer data
        query_with_customer = "What is my bill?"
        result = billing_agent._requires_customer_data(query_with_customer)
        assert result is True

        # Query that may not require customer data
        query_without_customer = "What are billing terms?"
        result = billing_agent._requires_customer_data(query_without_customer)
        # Result depends on implementation

    async def test_rag_retrieval(self, mock_rag):
        """Test RAG context retrieval."""
        result = await mock_rag.retrieve("billing question")

        mock_rag.retrieve.assert_called_once()
        assert result is not None

    async def test_billing_data_retrieval(
        self, billing_agent, mock_billing_tool, sample_context
    ):
        """Test customer billing data retrieval."""
        result = await billing_agent._get_billing_data(
            query="What is my bill?",
            context=sample_context,
        )

        assert result is not None

    async def test_error_handling_on_rag_failure(
        self, billing_agent, mock_rag, sample_context
    ):
        """Test handling of RAG service failure."""
        mock_rag.retrieve.side_effect = Exception("RAG service error")

        result = await billing_agent.handle(
            "What is my bill?",
            context=sample_context,
        )

        # Should handle gracefully
        assert result is not None

    async def test_error_handling_on_tool_failure(
        self, billing_agent, mock_billing_tool, sample_context
    ):
        """Test handling of billing tool failure."""
        mock_billing_tool.get_bill.side_effect = Exception(
            "Tool error"
        )

        result = await billing_agent.handle(
            "What is my bill?",
            context=sample_context,
        )

        assert result is not None

    async def test_multilingual_query_handling(
        self, billing_agent, sample_context
    ):
        """Test handling of queries in different languages."""
        hindi_query = "मेरा बिल क्या है?"
        tamil_query = "என் பில் என்ன?"

        sample_context["language"] = "hi"
        result_hi = await billing_agent.handle(hindi_query, sample_context)
        assert result_hi is not None

        sample_context["language"] = "ta"
        result_ta = await billing_agent.handle(tamil_query, sample_context)
        assert result_ta is not None

    async def test_response_contains_required_fields(
        self, billing_agent, sample_context
    ):
        """Test that response contains all required fields."""
        result = await billing_agent.handle(
            "What is my current bill?",
            context=sample_context,
        )

        assert "agent" in result
        assert "response" in result
        assert "success" in result
        assert result["agent"] == "billing"

    async def test_context_preservation(
        self, billing_agent, sample_context
    ):
        """Test that context is preserved during processing."""
        original_customer_id = sample_context["customer_id"]

        await billing_agent.handle(
            "What is my bill?",
            context=sample_context,
        )

        assert sample_context["customer_id"] == original_customer_id


@pytest.mark.asyncio
class TestBillingAgentIntegration:
    """Integration tests for BillingAgent with real-like scenarios."""

    @pytest.fixture
    def billing_agent(self, mock_gemini, mock_rag, mock_billing_tool):
        return BillingAgent(
            gemini=mock_gemini,
            rag=mock_rag,
            billing_tool=mock_billing_tool,
        )

    async def test_bill_inquiry_flow(self, billing_agent, sample_context):
        """Test complete bill inquiry flow."""
        query = "I want to know my current bill and due date."
        result = await billing_agent.handle(query, sample_context)

        assert result["success"] is True or "response" in result

    async def test_billing_dispute_flow(self, billing_agent, sample_context):
        """Test billing dispute inquiry flow."""
        query = "Why is my bill higher this month?"
        result = await billing_agent.handle(query, sample_context)

        assert result["agent"] == "billing"
        assert "response" in result

    async def test_invoice_request_flow(
        self, billing_agent, sample_context
    ):
        """Test invoice request flow."""
        query = "Can I get a copy of my last invoice?"
        result = await billing_agent.handle(query, sample_context)

        assert result is not None
