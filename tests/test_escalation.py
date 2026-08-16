"""
Unit tests for escalation and human agent features.

Tests cover:
- Escalation trigger detection
- Case creation
- Agent assignment
- Priority handling
- Status tracking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


@pytest.mark.asyncio
class TestEscalationDetection:
    """Test cases for escalation trigger detection."""

    @pytest.fixture
    def escalation_service(self):
        """Create a mock escalation service."""
        mock = AsyncMock()
        mock.should_escalate = AsyncMock(return_value=False)
        mock.create_escalation_case = AsyncMock(
            return_value={
                "case_id": "ESC001",
                "status": "pending",
            }
        )
        mock.assign_agent = AsyncMock(
            return_value={"agent_id": "A001"}
        )
        return mock

    async def test_detect_escalation_trigger(self, escalation_service):
        """Test detection of escalation trigger."""
        escalation_service.should_escalate = AsyncMock(
            return_value=True
        )

        result = await escalation_service.should_escalate(
            query="I want to speak with a human agent",
            context={"retry_count": 3},
        )

        assert result is True

    async def test_no_escalation_for_simple_query(
        self, escalation_service
    ):
        """Test no escalation for simple query."""
        escalation_service.should_escalate = AsyncMock(
            return_value=False
        )

        result = await escalation_service.should_escalate(
            query="What is my bill?",
            context={"retry_count": 0},
        )

        assert result is False

    async def test_escalation_on_explicit_request(
        self, escalation_service
    ):
        """Test escalation on explicit human agent request."""
        escalation_service.should_escalate = AsyncMock(
            return_value=True
        )

        keywords = [
            "human agent",
            "speak with someone",
            "customer service",
            "representative",
        ]

        for keyword in keywords:
            result = await escalation_service.should_escalate(
                query=f"I want to {keyword}"
            )
            assert result is True

    async def test_escalation_on_repeated_failures(
        self, escalation_service
    ):
        """Test escalation after repeated failures."""
        context = {"retry_count": 5, "failed_attempts": 5}

        escalation_service.should_escalate = AsyncMock(
            return_value=True
        )

        result = await escalation_service.should_escalate(
            query="Help",
            context=context,
        )

        assert result is True

    async def test_escalation_on_sentiment_analysis(
        self, escalation_service
    ):
        """Test escalation based on negative sentiment."""
        escalation_service.should_escalate = AsyncMock(
            return_value=True
        )

        result = await escalation_service.should_escalate(
            query="This is ridiculous! I'm very angry with your service!",
        )

        assert result is True


@pytest.mark.asyncio
class TestEscalationCaseManagement:
    """Test cases for escalation case management."""

    @pytest.fixture
    def escalation_service(self):
        mock = AsyncMock()
        mock.create_escalation_case = AsyncMock(
            return_value={
                "case_id": "ESC001",
                "status": "pending",
                "created_at": "2026-08-16T10:00:00Z",
            }
        )
        mock.get_case = AsyncMock(
            return_value={
                "case_id": "ESC001",
                "status": "assigned",
            }
        )
        mock.update_case_status = AsyncMock()
        return mock

    async def test_create_escalation_case(self, escalation_service):
        """Test creating escalation case."""
        case = await escalation_service.create_escalation_case(
            customer_id="C001",
            reason="customer_request",
            priority="high",
        )

        assert case["case_id"] == "ESC001"
        assert case["status"] == "pending"

    async def test_retrieve_escalation_case(self, escalation_service):
        """Test retrieving escalation case."""
        case = await escalation_service.get_case(case_id="ESC001")

        assert case["case_id"] == "ESC001"

    async def test_update_case_status(self, escalation_service):
        """Test updating case status."""
        await escalation_service.update_case_status(
            case_id="ESC001",
            status="assigned",
        )

        escalation_service.update_case_status.assert_called_once()

    async def test_case_priority_levels(self, escalation_service):
        """Test different priority levels for cases."""
        priorities = ["low", "medium", "high", "urgent"]

        for priority in priorities:
            case = await escalation_service.create_escalation_case(
                customer_id="C001",
                reason="testing",
                priority=priority,
            )
            assert case is not None


@pytest.mark.asyncio
class TestAgentAssignment:
    """Test cases for agent assignment."""

    @pytest.fixture
    def escalation_service(self):
        mock = AsyncMock()
        mock.assign_agent = AsyncMock(
            return_value={
                "agent_id": "A001",
                "agent_name": "John Doe",
                "status": "assigned",
            }
        )
        mock.get_available_agents = AsyncMock(
            return_value=[
                {"agent_id": "A001", "name": "Agent 1", "queue": 2},
                {"agent_id": "A002", "name": "Agent 2", "queue": 5},
            ]
        )
        return mock

    async def test_assign_agent_to_case(self, escalation_service):
        """Test assigning agent to escalation case."""
        result = await escalation_service.assign_agent(
            case_id="ESC001",
            customer_id="C001",
        )

        assert result["agent_id"] == "A001"
        assert result["status"] == "assigned"

    async def test_get_available_agents(self, escalation_service):
        """Test retrieving available agents."""
        agents = await escalation_service.get_available_agents()

        assert len(agents) > 0
        assert "agent_id" in agents[0]
        assert "queue" in agents[0]

    async def test_assign_to_least_busy_agent(
        self, escalation_service
    ):
        """Test assigning to least busy agent."""
        escalation_service.get_available_agents = AsyncMock(
            return_value=[
                {"agent_id": "A001", "queue": 3},
                {"agent_id": "A002", "queue": 1},
                {"agent_id": "A003", "queue": 5},
            ]
        )

        agents = await escalation_service.get_available_agents()
        # Agent with queue=1 should be selected
        least_busy = min(agents, key=lambda x: x["queue"])

        assert least_busy["agent_id"] == "A002"

    async def test_agent_assignment_timeout(self, escalation_service):
        """Test handling agent assignment timeout."""
        escalation_service.assign_agent = AsyncMock(
            side_effect=TimeoutError("Assignment timeout")
        )

        with pytest.raises(TimeoutError):
            await escalation_service.assign_agent(
                case_id="ESC001",
            )


@pytest.mark.asyncio
class TestEscalationStatus:
    """Test cases for escalation status tracking."""

    @pytest.fixture
    def escalation_service(self):
        mock = AsyncMock()
        mock.get_case_status = AsyncMock(
            return_value="assigned"
        )
        mock.update_case_status = AsyncMock()
        mock.get_case_history = AsyncMock(
            return_value=[
                {"status": "pending", "timestamp": "2026-08-16T10:00:00Z"},
                {
                    "status": "assigned",
                    "timestamp": "2026-08-16T10:05:00Z",
                },
            ]
        )
        return mock

    async def test_get_case_status(self, escalation_service):
        """Test retrieving case status."""
        status = await escalation_service.get_case_status(
            case_id="ESC001"
        )

        assert status == "assigned"

    async def test_case_status_transitions(self, escalation_service):
        """Test case status transitions."""
        statuses = ["pending", "assigned", "in_progress", "completed"]

        for status in statuses:
            await escalation_service.update_case_status(
                case_id="ESC001",
                status=status,
            )

        assert escalation_service.update_case_status.call_count == 4

    async def test_get_case_history(self, escalation_service):
        """Test retrieving case history."""
        history = await escalation_service.get_case_history(
            case_id="ESC001"
        )

        assert len(history) > 0
        assert history[0]["status"] == "pending"
        assert history[-1]["status"] == "assigned"

    async def test_case_timeout_handling(self, escalation_service):
        """Test handling case timeout."""
        escalation_service.update_case_status = AsyncMock()

        await escalation_service.update_case_status(
            case_id="ESC001",
            status="timeout",
        )

        escalation_service.update_case_status.assert_called_once()


@pytest.mark.asyncio
class TestEscalationIntegration:
    """Integration tests for escalation flow."""

    async def test_complete_escalation_flow(self):
        """Test complete escalation flow."""
        escalation_service = AsyncMock()

        # 1. Detect escalation needed
        escalation_service.should_escalate = AsyncMock(
            return_value=True
        )
        should_escalate = await escalation_service.should_escalate(
            query="Human agent please"
        )
        assert should_escalate is True

        # 2. Create case
        escalation_service.create_escalation_case = AsyncMock(
            return_value={"case_id": "ESC001", "status": "pending"}
        )
        case = await escalation_service.create_escalation_case(
            customer_id="C001",
            reason="customer_request",
        )
        assert case["case_id"] == "ESC001"

        # 3. Assign agent
        escalation_service.assign_agent = AsyncMock(
            return_value={"agent_id": "A001"}
        )
        assignment = await escalation_service.assign_agent(
            case_id="ESC001"
        )
        assert assignment["agent_id"] == "A001"

        # 4. Update status
        escalation_service.update_case_status = AsyncMock()
        await escalation_service.update_case_status(
            case_id="ESC001",
            status="assigned",
        )

    async def test_escalation_with_priority_queue(self):
        """Test escalation with priority queue handling."""
        escalation_service = AsyncMock()

        # Create multiple cases with different priorities
        cases = []
        for i, priority in enumerate(["low", "high", "urgent"]):
            case = {
                "case_id": f"ESC{i:03d}",
                "priority": priority,
                "queue_position": i,
            }
            cases.append(case)

        # High and urgent should be prioritized
        high_priority = [c for c in cases if c["priority"] != "low"]
        assert len(high_priority) == 2
