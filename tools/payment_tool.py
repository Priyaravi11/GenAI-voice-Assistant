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

from backend.app.database import payments_collection


# ============================================================
# HELPER
# Get all payments belonging to a customer
# ============================================================

def _get_customer_payments(cust_id: str):
    """
    Retrieve all payment records belonging to a customer.

    Database structure:
    {
        "_id": ...,
        "metadata": {...},
        "payments": [
            {...},
            {...}
        ]
    }
    """

    document = payments_collection.find_one(
        {
            "payments": {
                "$elemMatch": {
                    "cust_id": cust_id
                }
            }
        },
        {
            "_id": 0,
            "payments": 1
        }
    )

    if document is None:
        return []

    payments = document.get("payments", [])

    customer_payments = [
        payment
        for payment in payments
        if payment.get("cust_id") == cust_id
    ]

    # Sort newest payment first
    customer_payments.sort(
        key=lambda payment: payment.get("payment_date", ""),
        reverse=True
    )

    return customer_payments


# ============================================================
# PAYMENT TOOL 1
# Get Payment Status
# ============================================================

def get_payment_status(cust_id: str):
    """
    Retrieve the status of the customer's latest payment.
    """

    try:

        customer_payments = _get_customer_payments(cust_id)

        if not customer_payments:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

        latest_payment = customer_payments[0]

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Payment status retrieved successfully",
            "status": latest_payment.get("status"),
            "data": latest_payment
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve payment status",
            "error": str(e)
        }


# ============================================================
# PAYMENT TOOL 2
# Get Payment History
# ============================================================

def get_payment_history(cust_id: str):
    """
    Retrieve all payment records for a customer.
    """

    try:

        customer_payments = _get_customer_payments(cust_id)

        if not customer_payments:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment history found for customer {cust_id}"
            }

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Payment history retrieved successfully",
            "count": len(customer_payments),
            "data": customer_payments
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve payment history",
            "error": str(e)
        }


# ============================================================
# PAYMENT TOOL 3
# Get Latest Payment
# ============================================================

def get_latest_payment(cust_id: str):
    """
    Retrieve the most recent payment made by a customer.
    """

    try:

        customer_payments = _get_customer_payments(cust_id)

        if not customer_payments:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

        latest_payment = customer_payments[0]

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Latest payment retrieved successfully",
            "data": latest_payment
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve latest payment",
            "error": str(e)
        }


# ============================================================
# PAYMENT TOOL 4
# Get Payment Issue
# ============================================================

def get_payment_issue(cust_id: str):
    """
    Check whether the customer's latest payment
    is pending, failed, successful, or has an unknown status.
    """

    try:

        customer_payments = _get_customer_payments(cust_id)

        if not customer_payments:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

        latest_payment = customer_payments[0]

        status = str(
            latest_payment.get("status", "")
        ).strip().lower()

        # ----------------------------------------------------
        # Pending
        # ----------------------------------------------------

        if status == "pending":
            return {
                "success": True,
                "customer_id": cust_id,
                "issue": "pending_payment",
                "message": "The latest payment is still pending.",
                "data": latest_payment
            }

        # ----------------------------------------------------
        # Failed
        # ----------------------------------------------------

        if status == "failed":
            return {
                "success": True,
                "customer_id": cust_id,
                "issue": "failed_payment",
                "message": "The latest payment has failed.",
                "data": latest_payment
            }

        # ----------------------------------------------------
        # Successful
        # ----------------------------------------------------

        if status == "successful":
            return {
                "success": True,
                "customer_id": cust_id,
                "issue": None,
                "message": "The latest payment was successful. No payment issue found.",
                "data": latest_payment
            }

        # ----------------------------------------------------
        # Unknown status
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "issue": "unknown_payment_status",
            "message": f"The latest payment has an unknown status: {latest_payment.get('status')}",
            "data": latest_payment
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve payment issue",
            "error": str(e)
        }