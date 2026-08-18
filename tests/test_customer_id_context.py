from backend.app.context import SessionContext


def test_pending_customer_id_request_accepts_tool_alias():
    context = SessionContext(session_id="session-pending")

    context.set_pending_customer_id_request(
        agent="billing",
        query="What is my bill?",
        tool="get_current_bill",
    )

    pending = context.get_pending_customer_id_request()

    assert pending["waiting_for_customer_id"] is True
    assert pending["agent"] == "billing"
    assert pending["query"] == "What is my bill?"
    assert pending["tool"] == "get_current_bill"


def test_pending_customer_id_request_can_be_cleared():
    context = SessionContext(session_id="session-clear")
    context.set_pending_customer_id_request(
        agent="plans",
        query="What plan am I currently using?",
        tool_name="get_current_plan",
    )

    context.clear_pending_customer_id_request()

    pending = context.get_pending_customer_id_request()
    assert pending["waiting_for_customer_id"] is False
    assert pending["agent"] is None
    assert pending["query"] is None
    assert pending["tool"] is None
