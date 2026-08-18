import pytest

from backend.app.context import remove_session
from backend.app.orchestrator import Orchestrator


class FakeSupervisor:
    async def handle(self, query, context):
        return {
            "agent": "billing",
            "confidence": 0.99,
            "reason": "billing request",
            "method": "test",
        }


class FakeBillingAgent:
    def __init__(self):
        self.calls = []

    async def handle(self, query, context):
        self.calls.append((query, context.get("customer_id")))

        if not context.get("customer_id"):
            return {
                "agent": "billing",
                "response": "Please provide your customer ID.",
                "success": True,
                "confidence": 1.0,
                "tool_used": "get_current_bill",
                "tool_result": None,
                "rag_context": None,
                "requires_customer_id": True,
            }

        return {
            "agent": "billing",
            "response": f"Bill found for {context['customer_id']}.",
            "success": True,
            "confidence": 0.95,
            "tool_used": "get_current_bill",
            "tool_result": {
                "success": True,
                "data": {
                    "customer_id": context["customer_id"],
                },
            },
            "rag_context": None,
            "requires_customer_id": False,
        }


@pytest.fixture
def orchestrator_with_fakes():
    orchestrator = Orchestrator()
    billing_agent = FakeBillingAgent()
    orchestrator.supervisor = FakeSupervisor()
    orchestrator.agents = {
        "billing": billing_agent,
        "general": billing_agent,
    }
    yield orchestrator, billing_agent
    remove_session("customer-id-flow")
    remove_session("customer-id-invalid")


async def test_orchestrator_stores_customer_id_request_and_resumes(
    orchestrator_with_fakes,
):
    orchestrator, billing_agent = orchestrator_with_fakes

    first_result = await orchestrator.process_text(
        session_id="customer-id-flow",
        customer_query="What is my current bill?",
        language="en",
    )

    assert first_result["requires_customer_id"] is True
    assert first_result["tool_name"] == "get_current_bill"

    second_result = await orchestrator.process_text(
        session_id="customer-id-flow",
        customer_query="C251",
        language="en",
    )

    assert second_result["requires_customer_id"] is False
    assert second_result["customer_id"] == "C251"
    assert second_result["method"] == "customer_id_resume"
    assert second_result["response"] == "Bill found for C251."
    assert billing_agent.calls == [
        ("What is my current bill?", None),
        ("What is my current bill?", "C251"),
    ]


async def test_orchestrator_keeps_pending_request_for_invalid_customer_id(
    orchestrator_with_fakes,
):
    orchestrator, billing_agent = orchestrator_with_fakes

    await orchestrator.process_text(
        session_id="customer-id-invalid",
        customer_query="What is my current bill?",
        language="en",
    )

    invalid_result = await orchestrator.process_text(
        session_id="customer-id-invalid",
        customer_query="C 251!",
        language="en",
    )

    assert invalid_result["requires_customer_id"] is True
    assert invalid_result["method"] == "customer_id_validation"

    resumed_result = await orchestrator.process_text(
        session_id="customer-id-invalid",
        customer_query="C251",
        language="en",
    )

    assert resumed_result["requires_customer_id"] is False
    assert resumed_result["response"] == "Bill found for C251."
    assert billing_agent.calls == [
        ("What is my current bill?", None),
        ("What is my current bill?", "C251"),
    ]
