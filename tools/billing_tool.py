import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import billing_collection

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
if __name__ == "__main__":

    customer_id = "C251"

    result = check_duplicate_bill(customer_id)

    print("\n========== DUPLICATE BILL CHECK ==========")
    print(result)
