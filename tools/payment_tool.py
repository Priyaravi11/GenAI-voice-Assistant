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
# PAYMENT TOOL 1
# Get Payment Status
# ============================================================

def get_payment_status(cust_id: str):
    """
    Retrieve the latest payment status for a customer.
    """

    try:

        latest_payment = payments_collection.find_one(
            {
                "cust_id": cust_id
            },
            {
                "_id": 0,
                "payment_id": 1,
                "cust_id": 1,
                "amount": 1,
                "payment_date": 1,
                "status": 1,
                "payment_method": 1,
                "transaction_id": 1,
                "failure_reason": 1
            },
            sort=[
                ("payment_date", -1)
            ]
        )

        if latest_payment is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Payment status retrieved successfully",
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

        payment_history = list(
            payments_collection.find(
                {
                    "cust_id": cust_id
                },
                {
                    "_id": 0,
                    "payment_id": 1,
                    "cust_id": 1,
                    "account_id": 1,
                    "bill_id": 1,
                    "amount": 1,
                    "payment_method": 1,
                    "payment_date": 1,
                    "status": 1,
                    "transaction_id": 1,
                    "failure_reason": 1,
                    "auto_pay": 1,
                    "auto_debit_status": 1,
                    "late_fee": 1,
                    "bounced_charge": 1,
                    "created_at": 1
                }
            ).sort(
                "payment_date",
                -1
            )
        )

        if not payment_history:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment history found for customer {cust_id}"
            }

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Payment history retrieved successfully",
            "count": len(payment_history),
            "data": payment_history
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

        latest_payment = payments_collection.find_one(
            {
                "cust_id": cust_id
            },
            {
                "_id": 0,
                "payment_id": 1,
                "cust_id": 1,
                "account_id": 1,
                "bill_id": 1,
                "amount": 1,
                "payment_method": 1,
                "payment_date": 1,
                "status": 1,
                "transaction_id": 1,
                "failure_reason": 1,
                "auto_pay": 1,
                "auto_debit_status": 1,
                "late_fee": 1,
                "bounced_charge": 1,
                "created_at": 1
            },
            sort=[
                ("payment_date", -1)
            ]
        )

        if latest_payment is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

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
    is pending or failed.
    """

    try:

        latest_payment = payments_collection.find_one(
            {
                "cust_id": cust_id
            },
            {
                "_id": 0,
                "payment_id": 1,
                "cust_id": 1,
                "account_id": 1,
                "bill_id": 1,
                "amount": 1,
                "payment_method": 1,
                "payment_date": 1,
                "status": 1,
                "transaction_id": 1,
                "failure_reason": 1
            },
            sort=[
                ("payment_date", -1)
            ]
        )

        if latest_payment is None:

            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No payment record found for customer {cust_id}"
            }

        status = latest_payment.get("status")

        # Pending payment
        if status == "pending":

            return {
                "success": True,
                "customer_id": cust_id,
                "issue": "pending_payment",
                "message": "The latest payment is still pending.",
                "data": latest_payment
            }

        # Failed payment
        if status == "failed":

            return {
                "success": True,
                "customer_id": cust_id,
                "issue": "failed_payment",
                "message": "The latest payment has failed.",
                "data": latest_payment
            }

        # Successful payment
        if status == "successful":

            return {
                "success": True,
                "customer_id": cust_id,
                "issue": None,
                "message": "The latest payment was successful. No payment issue found.",
                "data": latest_payment
            }

        # Unknown status
        return {
            "success": True,
            "customer_id": cust_id,
            "issue": "unknown_payment_status",
            "message": f"The latest payment has an unknown status: {status}",
            "data": latest_payment
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve payment issue",
            "error": str(e)
        }