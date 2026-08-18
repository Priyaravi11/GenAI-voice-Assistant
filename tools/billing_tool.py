import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import (
    billing_collection,
    plans_collection,
)


# ============================================================
# BILLING TOOL 1
# Get Current Bill
# ============================================================

def get_current_bill(cust_id: str):
    """
    Get the latest bill for a customer.

    The billing records are stored inside the
    'bills' array of telecom_billing_history.
    """

    try:

        # Find the billing document that contains this customer
        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Get all bills belonging to this customer
        customer_bills = [
            bill
            for bill in document["bills"]
            if bill.get("cust_id") == cust_id
        ]

        # No bills for customer
        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Sort bills by bill_date
        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        # Latest bill
        current_bill = customer_bills[0]

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Current bill retrieved successfully",
            "data": current_bill
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve current bill",
            "error": str(e)
        }


# ============================================================
# BILLING TOOL 2
# Get Previous Bill
# ============================================================

def get_previous_bill(cust_id: str):
    """
    Get the bill immediately before the customer's current bill.
    """

    try:

        # Find the billing document containing this customer
        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Get all bills belonging to this customer
        customer_bills = [
            bill
            for bill in document["bills"]
            if bill.get("cust_id") == cust_id
        ]

        # No bills found
        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Sort newest → oldest
        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        # Need at least two bills
        if len(customer_bills) < 2:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Previous bill is not available"
            }

        # Second latest bill = previous bill
        previous_bill = customer_bills[1]

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Previous bill retrieved successfully",
            "data": previous_bill
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve previous bill",
            "error": str(e)
        }


# ============================================================
# BILLING TOOL 3
# Get Bill History
# ============================================================

def get_bill_history(cust_id: str):
    """
    Get complete billing history for a customer.
    """

    try:

        # Find the billing document containing this customer
        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing history found for customer {cust_id}"
            }

        # Get all bills for this customer
        customer_bills = [
            bill
            for bill in document["bills"]
            if bill.get("cust_id") == cust_id
        ]

        # No bills found
        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing history found for customer {cust_id}"
            }

        # Sort newest → oldest
        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Billing history retrieved successfully",
            "total_bills": len(customer_bills),
            "data": customer_bills
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve billing history",
            "error": str(e)
        }


# ============================================================
# BILLING TOOL 4
# Check Duplicate Bill
# ============================================================

def check_duplicate_bill(cust_id: str):
    """
    Check whether a customer has duplicate bills
    for the same billing period.
    """

    try:

        # Find billing document containing this customer
        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Get all bills belonging to this customer
        customer_bills = [
            bill
            for bill in document.get("bills", [])
            if bill.get("cust_id") == cust_id
        ]

        # No bills found
        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Group bills by billing period
        period_groups = {}

        for bill in customer_bills:

            billing_period = bill.get("billing_period")

            if billing_period not in period_groups:
                period_groups[billing_period] = []

            period_groups[billing_period].append(bill)

        # Find duplicate billing periods
        duplicate_bills = []

        for billing_period, bills in period_groups.items():

            if len(bills) > 1:

                duplicate_bills.append({
                    "billing_period": billing_period,
                    "count": len(bills),
                    "bills": bills
                })

        # No duplicates
        if not duplicate_bills:
            return {
                "success": True,
                "customer_id": cust_id,
                "duplicate_found": False,
                "message": "No duplicate bills found"
            }

        # Duplicate found
        return {
            "success": True,
            "customer_id": cust_id,
            "duplicate_found": True,
            "message": "Duplicate bill(s) found",
            "duplicate_bills": duplicate_bills
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to check duplicate bills",
            "error": str(e)
        }


# ============================================================
# BILLING TOOL 5
# Check High Bill
# ============================================================

def check_high_bill(cust_id: str):
    """
    Check whether the customer's current bill is unusually high
    compared with their previous billing history.

    A bill is considered high when it is at least 30% higher
    than the customer's average previous bill.
    """

    try:

        # Find the billing document containing this customer
        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Get all bills belonging to this customer
        customer_bills = [
            bill
            for bill in document.get("bills", [])
            if bill.get("cust_id") == cust_id
        ]

        # No bills found
        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # Sort newest → oldest
        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        # Need at least 2 bills for comparison
        if len(customer_bills) < 2:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Not enough billing history to determine whether the bill is high"
            }

        # Current/latest bill
        current_bill = customer_bills[0]

        # Previous bills
        previous_bills = customer_bills[1:]

        # Get valid previous bill amounts
        previous_amounts = []

        for bill in previous_bills:

            amount = bill.get("amount")

            if amount is not None:

                try:
                    previous_amounts.append(float(amount))
                except (ValueError, TypeError):
                    continue

        # No valid previous amounts
        if not previous_amounts:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Previous bill amounts are not available for comparison"
            }

        # Current bill amount
        current_amount = current_bill.get("amount")

        if current_amount is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Current bill amount is not available"
            }

        try:
            current_amount = float(current_amount)
        except (ValueError, TypeError):

            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Current bill amount is invalid"
            }

        # Calculate historical average
        average_previous_bill = sum(previous_amounts) / len(previous_amounts)

        # High bill threshold = 30% above average
        threshold_percentage = 30

        high_bill_threshold = (
            average_previous_bill
            * (1 + threshold_percentage / 100)
        )

        # Determine whether current bill is high
        high_bill = current_amount > high_bill_threshold

        # Calculate percentage increase
        percentage_increase = (
            (current_amount - average_previous_bill)
            / average_previous_bill
        ) * 100

        return {
            "success": True,
            "customer_id": cust_id,
            "high_bill": high_bill,
            "message": (
                "High bill detected"
                if high_bill
                else "Bill is within the normal range"
            ),
            "data": {
                "current_bill_id": current_bill.get("bill_id"),
                "current_bill_amount": current_amount,
                "average_previous_bill": round(
                    average_previous_bill, 2
                ),
                "high_bill_threshold": round(
                    high_bill_threshold, 2
                ),
                "percentage_increase": round(
                    percentage_increase, 2
                ),
                "previous_bills_considered": len(
                    previous_amounts
                )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to check high bill",
            "error": str(e)
        }


# ============================================================
# BILLING TOOL 6
# Check Incorrect Plan Charge
# ============================================================

def check_incorrect_plan_charge(cust_id: str):
    """
    Check whether the customer was charged an incorrect amount
    compared with the expected charge of their subscribed plan.
    """

    try:

        # ----------------------------------------------------
        # Find the billing document containing this customer
        # ----------------------------------------------------

        document = billing_collection.find_one(
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

        # Customer not found
        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get all bills belonging to this customer
        # ----------------------------------------------------

        customer_bills = [
            bill
            for bill in document.get("bills", [])
            if bill.get("cust_id") == cust_id
        ]

        if not customer_bills:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No billing record found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Sort bills newest → oldest
        # ----------------------------------------------------

        customer_bills.sort(
            key=lambda bill: bill.get("bill_date", ""),
            reverse=True
        )

        # Latest/current bill
        current_bill = customer_bills[0]

        # ----------------------------------------------------
        # Get plan ID
        # ----------------------------------------------------

        plan_id = current_bill.get("plan_id")

        if not plan_id:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Plan ID is not available in the current bill"
            }

        # ----------------------------------------------------
        # Get actual billed amount
        # ----------------------------------------------------

        billed_amount = current_bill.get("amount")

        if billed_amount is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Bill amount is not available"
            }

        try:
            billed_amount = float(billed_amount)

        except (ValueError, TypeError):
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Bill amount is invalid"
            }

        # ----------------------------------------------------
        # Find the subscribed plan
        # ----------------------------------------------------

        plan = plans_collection.find_one(
            {
                "plan_id": plan_id
            },
            {
                "_id": 0
            }
        )

        if plan is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "plan_id": plan_id,
                "message": f"No plan found for plan ID {plan_id}"
            }

        # ----------------------------------------------------
        # Get expected plan charge
        # ----------------------------------------------------

        expected_charge = plan.get("monthly_charge")

        if expected_charge is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "plan_id": plan_id,
                "message": "Expected monthly plan charge is not available"
            }

        try:
            expected_charge = float(expected_charge)

        except (ValueError, TypeError):
            return {
                "success": False,
                "customer_id": cust_id,
                "plan_id": plan_id,
                "message": "Expected plan charge is invalid"
            }

        # ----------------------------------------------------
        # Compare billed amount with expected plan charge
        # ----------------------------------------------------

        difference = round(
            billed_amount - expected_charge,
            2
        )

        incorrect_charge = difference != 0

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "incorrect_plan_charge": incorrect_charge,
            "message": (
                "Incorrect plan charge detected"
                if incorrect_charge
                else "Plan charge is correct"
            ),
            "data": {
                "bill_id": current_bill.get("bill_id"),
                "plan_id": plan_id,
                "plan_name": plan.get("plan_name"),
                "billed_amount": billed_amount,
                "expected_plan_charge": expected_charge,
                "difference": difference
            }
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to check incorrect plan charge",
            "error": str(e)
        }
    
