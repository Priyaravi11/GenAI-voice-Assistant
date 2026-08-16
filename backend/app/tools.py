"""
Central Tool Registry
File: backend/app/tools/tools.py

This file collects all available telecom tools
and provides them through a single TOOL_REGISTRY.

The orchestrator/agents can use this registry
to access the required tool by name.
"""

from .billing_tool import (
    get_current_bill,
    get_previous_bill,
    get_bill_history,
    check_duplicate_bill,
)

from .customer_tool import (
    get_customer_profile,
    get_customer_account,
    get_customer_plan,
    get_customer_service,
    get_customer_area,
    get_customer_usage,
    get_customer_vas,
    get_customer_autopay,
)

from .network_tool import (
    get_network_status,
    get_network_issue,
    get_resolution_time,
    check_area_service,
    get_network_details,
)

from .payment_tool import (
    get_payment_status,
    get_payment_history,
    get_latest_payment,
    get_payment_issue,
)

from .plans_tool import (
    get_plan_details,
    compare_plans,
    find_plans,
    get_plan_change_info,
)


# ============================================================
# CENTRAL TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {

    # --------------------------------------------------------
    # BILLING TOOLS
    # --------------------------------------------------------

    "get_current_bill": get_current_bill,
    "get_previous_bill": get_previous_bill,
    "get_bill_history": get_bill_history,
    "check_duplicate_bill": check_duplicate_bill,

    # --------------------------------------------------------
    # CUSTOMER TOOLS
    # --------------------------------------------------------

    "get_customer_profile": get_customer_profile,
    "get_customer_account": get_customer_account,
    "get_customer_plan": get_customer_plan,
    "get_customer_service": get_customer_service,
    "get_customer_area": get_customer_area,
    "get_customer_usage": get_customer_usage,
    "get_customer_vas": get_customer_vas,
    "get_customer_autopay": get_customer_autopay,

    # --------------------------------------------------------
    # NETWORK TOOLS
    # --------------------------------------------------------

    "get_network_status": get_network_status,
    "get_network_issue": get_network_issue,
    "get_resolution_time": get_resolution_time,
    "check_area_service": check_area_service,
    "get_network_details": get_network_details,

    # --------------------------------------------------------
    # PAYMENT TOOLS
    # --------------------------------------------------------

    "get_payment_status": get_payment_status,
    "get_payment_history": get_payment_history,
    "get_latest_payment": get_latest_payment,
    "get_payment_issue": get_payment_issue,

    # --------------------------------------------------------
    # PLAN TOOLS
    # --------------------------------------------------------

    "get_plan_details": get_plan_details,
    "compare_plans": compare_plans,
    "find_plans": find_plans,
    "get_plan_change_info": get_plan_change_info,
}


# ============================================================
# TOOL EXECUTION HELPER
# ============================================================

def get_tool(tool_name: str):
    """
    Get a tool function by its registered name.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    return TOOL_REGISTRY[tool_name]


def list_tools():
    """
    Return all available tool names.
    """

    return list(TOOL_REGISTRY.keys())