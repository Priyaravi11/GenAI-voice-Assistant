import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# DATABASE
# ============================================================

from backend.app.database import plans_collection


def _get_plans_document():
    return plans_collection.find_one(
        {},
        {
            "_id": 0,
            "plans": 1
        }
    )


def get_available_plans():
    """
    Retrieve all available telecom plans.
    """

    try:
        document = _get_plans_document()

        if document is None:
            return {
                "success": False,
                "message": "Plan database is empty"
            }

        plans = document.get("plans", [])

        return {
            "success": True,
            "message": "Available plans retrieved successfully",
            "count": len(plans),
            "data": plans
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to retrieve available plans",
            "error": str(e)
        }


def get_current_plan(cust_id: str):
    """
    Retrieve the customer's current plan from their latest billing record.
    """

    try:
        from backend.app.database import billing_collection

        billing_document = billing_collection.find_one(
            {
                "bills": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "bills": 1
            }
        )

        if billing_document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        customer_bills = [
            bill
            for bill in billing_document.get("bills", [])
            if bill.get("cust_id") == cust_id
        ]

        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        current_plan_id = customer_bills[0].get("plan_id")

        if not current_plan_id:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Current plan information is not available"
            }

        plan_result = get_plan_details(current_plan_id)

        if not plan_result.get("success"):
            return plan_result

        return {
            "success": True,
            "customer_id": cust_id,
            "plan_id": current_plan_id,
            "message": "Current plan retrieved successfully",
            "data": plan_result.get("data")
        }

    except Exception as e:
        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve current plan",
            "error": str(e)
        }


# ============================================================
# PLAN TOOL 1
# Get Plan Details
# ============================================================

def get_plan_details(plan_id: str):
    """
    Retrieve details of a telecom plan using plan ID.
    """

    try:

        document = plans_collection.find_one(
            {},
            {
                "_id": 0,
                "plans": 1
            }
        )

        if document is None:

            return {
                "success": False,
                "plan_id": plan_id,
                "message": "Plan database is empty"
            }

        plan = next(
            (
                p for p in document.get("plans", [])
                if p.get("plan_id") == plan_id
            ),
            None
        )

        if plan is None:

            return {
                "success": False,
                "plan_id": plan_id,
                "message": f"No plan found for plan ID {plan_id}"
            }

        return {
            "success": True,
            "plan_id": plan_id,
            "message": "Plan details retrieved successfully",
            "data": plan
        }

    except Exception as e:

        return {
            "success": False,
            "plan_id": plan_id,
            "message": "Failed to retrieve plan details",
            "error": str(e)
        }


# ============================================================
# PLAN TOOL 2
# Compare Plans
# ============================================================

def compare_plans(plan_id_1: str, plan_id_2: str):
    """
    Compare two telecom plans.
    """

    try:

        document = plans_collection.find_one(
            {},
            {
                "_id": 0,
                "plans": 1
            }
        )

        if document is None:

            return {
                "success": False,
                "message": "Plan database is empty"
            }

        plans = document.get("plans", [])

        plan_1 = next(
            (
                p for p in plans
                if p.get("plan_id") == plan_id_1
            ),
            None
        )

        plan_2 = next(
            (
                p for p in plans
                if p.get("plan_id") == plan_id_2
            ),
            None
        )

        if plan_1 is None:

            return {
                "success": False,
                "plan_id": plan_id_1,
                "message": f"No plan found for plan ID {plan_id_1}"
            }

        if plan_2 is None:

            return {
                "success": False,
                "plan_id": plan_id_2,
                "message": f"No plan found for plan ID {plan_id_2}"
            }

        price_difference = (
            plan_2.get("price", 0)
            - plan_1.get("price", 0)
        )

        return {
            "success": True,
            "message": "Plans compared successfully",
            "data": {
                "plan_1": plan_1,
                "plan_2": plan_2,
                "price_difference": price_difference
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": "Failed to compare plans",
            "error": str(e)
        }


# ============================================================
# PLAN TOOL 3
# Find Plans
# ============================================================

def find_plans(
    max_price=None,
    min_data_gb=None,
    plan_type=None,
    roaming_required=None
):
    """
    Find telecom plans based on optional filters.
    """

    try:

        document = plans_collection.find_one(
            {},
            {
                "_id": 0,
                "plans": 1
            }
        )

        if document is None:

            return {
                "success": False,
                "message": "Plan database is empty"
            }

        plans = document.get("plans", [])

        filtered_plans = []

        for plan in plans:

            # Maximum price
            if max_price is not None:

                if plan.get("price", 0) > float(max_price):
                    continue

            # Minimum data
            if min_data_gb is not None:

                if plan.get("data_limit_gb", 0) < float(min_data_gb):
                    continue

            # Plan type
            if plan_type is not None:

                if plan.get("plan_type", "").lower() != str(
                    plan_type
                ).lower():

                    continue

            # Roaming
            if roaming_required is not None:

                if plan.get("roaming_included") != roaming_required:
                    continue

            filtered_plans.append(plan)

        return {
            "success": True,
            "message": "Plans retrieved successfully",
            "count": len(filtered_plans),
            "data": filtered_plans
        }

    except Exception as e:

        return {
            "success": False,
            "message": "Failed to find plans",
            "error": str(e)
        }


# ============================================================
# PLAN TOOL 4
# Get Plan Change Information
# ============================================================

def get_plan_change_info(cust_id: str, new_plan_id: str):
    """
    Retrieve the customer's current plan and compare it
    with the requested new plan.

    The customer's current plan is retrieved from the
    telecom billing records through the customer billing data.
    """

    try:

        # Import here to avoid unnecessary dependency
        # when this function is not used.
        from backend.app.database import billing_collection

        # ----------------------------------------------------
        # Get customer's latest bill
        # ----------------------------------------------------

        billing_document = billing_collection.find_one(
            {
                "bills": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "bills": 1
            }
        )

        if billing_document is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        customer_bills = [
            bill
            for bill in billing_document.get("bills", [])
            if bill.get("cust_id") == cust_id
        ]

        if not customer_bills:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        current_bill = customer_bills[0]

        current_plan_id = current_bill.get("plan_id")

        if not current_plan_id:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Current plan information is not available"
            }

        # ----------------------------------------------------
        # Get plans
        # ----------------------------------------------------

        document = plans_collection.find_one(
            {},
            {
                "_id": 0,
                "plans": 1
            }
        )

        if document is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Plan database is empty"
            }

        plans = document.get("plans", [])

        current_plan = next(
            (
                plan for plan in plans
                if plan.get("plan_id") == current_plan_id
            ),
            None
        )

        new_plan = next(
            (
                plan for plan in plans
                if plan.get("plan_id") == new_plan_id
            ),
            None
        )

        if current_plan is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"Current plan {current_plan_id} was not found"
            }

        if new_plan is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"New plan {new_plan_id} was not found"
            }

        # ----------------------------------------------------
        # Calculate price difference
        # ----------------------------------------------------

        price_difference = (
            new_plan.get("price", 0)
            - current_plan.get("price", 0)
        )

        if price_difference > 0:
            change_type = "upgrade"

        elif price_difference < 0:
            change_type = "downgrade"

        else:
            change_type = "same_price"

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Plan change information retrieved successfully",
            "data": {
                "current_plan": current_plan,
                "new_plan": new_plan,
                "price_difference": price_difference,
                "change_type": change_type
            }
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve plan change information",
            "error": str(e)
        }
