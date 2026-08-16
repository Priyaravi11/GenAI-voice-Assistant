"""
Test script for escalation.py
File: tests/test_escalation.py

Tests should_escalate() against the REAL return shapes produced by
billing_agent.py, general_agent.py, payment_agent.py, plans_agent.py,
and technical_agent.py — not a generic "escalate" flag, since none of
them set one directly.

Run from project root:
    python tests/test_escalation.py
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
_BACKEND_APP = os.path.join(_PROJECT_ROOT, "backend", "app")
if _BACKEND_APP not in sys.path:
    sys.path.insert(0, _BACKEND_APP)

from escalation import EscalationManager


def run_test(name, agent_result, expected_escalate, context=None):
    manager = EscalationManager()
    context = context or {"language": "English"}

    actual = manager.should_escalate(agent_result)
    status = "PASS" if actual == expected_escalate else "FAIL"

    print(f"[{status}] {name} -> should_escalate={actual} (expected {expected_escalate})")

    if actual and status == "PASS":
        result = manager.handle_escalation(reason=agent_result.get("agent", "unknown"), context=context)
        print(f"       message: {result['response'][:60]}...")

    return status == "PASS"


def main():
    results = []

    # --- billing_agent.py real shapes ---
    results.append(run_test(
        "billing - success True (no escalate)",
        {"agent": "billing", "response": "Your bill is ₹799", "success": True, "tool_used": "get_current_bill"},
        expected_escalate=False,
    ))
    results.append(run_test(
        "billing - success False (escalate)",
        {"agent": "billing", "response": "I'm sorry, I couldn't process your billing request right now.", "success": False},
        expected_escalate=True,
    ))

    # --- payment_agent.py real shapes ---
    results.append(run_test(
        "payment - success True (no escalate)",
        {"agent": "payment", "response": "Your payment went through", "success": True},
        expected_escalate=False,
    ))
    results.append(run_test(
        "payment - success False (escalate)",
        {"agent": "payment", "response": "I'm sorry, I couldn't process your payment request right now.", "success": False},
        expected_escalate=True,
    ))

    # --- plans_agent.py real shapes ---
    results.append(run_test(
        "plans - used_rag True (no escalate)",
        {"agent": "plans", "used_rag": True, "used_tool": False, "tool_name": None, "tool_data": None, "response": "Here are prepaid plans..."},
        expected_escalate=False,
    ))
    results.append(run_test(
        "plans - used_tool True with tool success (no escalate)",
        {"agent": "plans", "used_rag": False, "used_tool": True, "tool_name": "get_current_plan",
         "tool_data": {"success": True, "message": "Plan found", "data": {"plan": "Unlimited 5G"}},
         "response": "You're on the Unlimited 5G plan"},
        expected_escalate=False,
    ))
    results.append(run_test(
        "plans - neither rag nor tool used (escalate)",
        {"agent": "plans", "used_rag": False, "used_tool": False, "tool_name": None, "tool_data": None,
         "response": "I couldn't find specific plan information for your request."},
        expected_escalate=True,
    ))
    results.append(run_test(
        "plans - tool used but tool itself failed (escalate)",
        {"agent": "plans", "used_rag": False, "used_tool": True, "tool_name": "get_plan_details",
         "tool_data": {"success": False, "message": "Plan ID is required to retrieve plan details."},
         "response": "Plan ID is required to retrieve plan details."},
        expected_escalate=True,
    ))

    # --- technical_agent.py real shapes (same pattern as plans) ---
    results.append(run_test(
        "technical - used_tool True with success (no escalate)",
        {"agent": "technical", "used_rag": False, "used_tool": True, "tool_name": "get_network_status",
         "tool_data": {"success": True, "message": "Network is up", "data": {"status": "operational"}},
         "response": "Your network is operational"},
        expected_escalate=False,
    ))
    results.append(run_test(
        "technical - neither rag nor tool used (escalate)",
        {"agent": "technical", "used_rag": False, "used_tool": False, "tool_name": None, "tool_data": None,
         "response": "I couldn't find specific network information for your request."},
        expected_escalate=True,
    ))

    # --- verified against REAL tool output shapes (billing_tool.py, network_tool.py) ---
    results.append(run_test(
        "plans - real plans_tool.py 'not found' shape (escalate)",
        {"agent": "plans", "used_rag": False, "used_tool": True, "tool_name": "get_plan_details",
         "tool_data": {"success": False, "plan_id": "P999", "message": "No plan found for plan ID P999"},
         "response": "No plan found for plan ID P999"},
        expected_escalate=True,
    ))
    results.append(run_test(
        "technical - real network_tool.py 'not found' shape (escalate)",
        {"agent": "technical", "used_rag": False, "used_tool": True, "tool_name": "get_network_status",
         "tool_data": {"success": False, "area": "Nowhereville", "message": "No network information found for area Nowhereville"},
         "response": "No network information found for area Nowhereville"},
        expected_escalate=True,
    ))
    results.append(run_test(
        "technical - real network_tool.py 'no issue reported' shape (success=True, no escalate)",
        {"agent": "technical", "used_rag": False, "used_tool": True, "tool_name": "get_network_issue",
         "tool_data": {"success": True, "area": "Chennai", "message": "No network issue reported for this area",
                        "data": {"area": "Chennai", "issue": None}},
         "response": "No issues reported in your area"},
        expected_escalate=False,
    ))

    # --- general_agent.py: the important edge case ---
    # General ALWAYS has used_rag=False, used_tool=False by design.
    # This must NOT escalate — that would break every greeting/thanks message.
    results.append(run_test(
        "general - used_rag/used_tool always False by design (must NOT escalate)",
        {"agent": "general", "used_rag": False, "used_tool": False, "rag_context": [], "tool_data": None,
         "response": "Hello! How can I help you today?"},
        expected_escalate=False,
    ))

    # --- language coverage on the escalation message itself ---
    for lang in ["English", "Tamil", "Hindi", "Telugu", "Kannada", "Malayalam"]:
        results.append(run_test(
            f"escalation message renders - {lang}",
            {"agent": "billing", "success": False},
            expected_escalate=True,
            context={"language": lang},
        ))

    print(f"\n{sum(results)}/{len(results)} passed")


if __name__ == "__main__":
    main()