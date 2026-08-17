import sys
from pathlib import Path

# ============================================================
# Add project root to Python path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import db


# ============================================================
# CUSTOMER TOOL 1
# Get Customer Profile
# ============================================================

def get_customer_profile(cust_id: str):
    """
    Get the customer's profile information from
    the accounts array.
    """

    try:

        # ----------------------------------------------------
        # Find the document containing this customer
        # ----------------------------------------------------

        document = db["telecom_account"].find_one(
            {
                "accounts": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "accounts": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No customer profile found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Find the customer's account/profile
        # ----------------------------------------------------

        customer_profile = None

        for account in document.get("accounts", []):

            if account.get("cust_id") == cust_id:
                customer_profile = account
                break

        # ----------------------------------------------------
        # Customer not found inside accounts
        # ----------------------------------------------------

        if customer_profile is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No customer profile found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return customer profile
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer profile retrieved successfully",
            "data": customer_profile
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer profile",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 2
# Get Customer Account
# ============================================================

def get_customer_account(cust_id: str):
    """
    Get the customer's account information.
    """

    try:

        # ----------------------------------------------------
        # Find the document containing this customer
        # ----------------------------------------------------

        document = db["telecom_account"].find_one(
            {
                "accounts": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "accounts": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No account found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Find customer's account
        # ----------------------------------------------------

        customer_account = None

        for account in document.get("accounts", []):

            if account.get("cust_id") == cust_id:
                customer_account = account
                break

        # ----------------------------------------------------
        # Account not found
        # ----------------------------------------------------

        if customer_account is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No account found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return account information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer account retrieved successfully",
            "data": customer_account
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer account",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 3
# Get Customer Plan
# ============================================================

def get_customer_plan(cust_id: str):
    """
    Get the plan subscribed by the customer.
    """

    try:

        # ----------------------------------------------------
        # Find customer's account
        # ----------------------------------------------------

        account_document = db["telecom_account"].find_one(
            {
                "accounts": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "accounts": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if account_document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No account found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Find customer's account
        # ----------------------------------------------------

        customer_account = None

        for account in account_document.get("accounts", []):

            if account.get("cust_id") == cust_id:
                customer_account = account
                break

        if customer_account is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No account found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get plan ID
        # ----------------------------------------------------

        plan_id = customer_account.get("plan_id")

        if not plan_id:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": "Plan ID is not available for this customer"
            }

        # ----------------------------------------------------
        # Find plan details
        # ----------------------------------------------------

        plan_document = db["telecom_plans"].find_one(
            {
                "plan_id": plan_id
            },
            {
                "_id": 0
            }
        )

        # ----------------------------------------------------
        # Plan not found
        # ----------------------------------------------------

        if plan_document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "plan_id": plan_id,
                "message": f"No plan found for plan ID {plan_id}"
            }

        # ----------------------------------------------------
        # Return plan details
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "plan_id": plan_id,
            "message": "Customer plan retrieved successfully",
            "data": plan_document
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer plan",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 4
# Get Customer Service
# ============================================================

def get_customer_service(cust_id: str):
    """
    Get the service information of a customer.
    """

    try:

        # ----------------------------------------------------
        # Find the document containing this customer
        # ----------------------------------------------------

        document = db["telecom_service"].find_one(
            {
                "services": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "services": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No service information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Find customer's service
        # ----------------------------------------------------

        customer_service = []

        for service in document.get("services", []):

            if service.get("cust_id") == cust_id:
                customer_service.append(service)

        # ----------------------------------------------------
        # Service not found
        # ----------------------------------------------------

        if not customer_service:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No service information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return service information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer service information retrieved successfully",
            "data": customer_service
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer service information",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 5
# Get Customer Area
# ============================================================

def get_customer_area(cust_id: str):
    """
    Get the area information of a customer.
    """

    try:

        # ----------------------------------------------------
        # Find the customer's service record
        # ----------------------------------------------------

        document = db["telecom_service"].find_one(
            {
                "services": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "services": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No area information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get customer's service records
        # ----------------------------------------------------

        customer_services = [
            service
            for service in document.get("services", [])
            if service.get("cust_id") == cust_id
        ]

        # ----------------------------------------------------
        # No service record found
        # ----------------------------------------------------

        if not customer_services:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No area information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Find area
        # ----------------------------------------------------

        area = None

        for service in customer_services:

            if service.get("area"):
                area = service.get("area")
                break

        # ----------------------------------------------------
        # Area not available
        # ----------------------------------------------------

        if area is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"Area information is not available for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return area
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer area retrieved successfully",
            "data": {
                "area": area
            }
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer area",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 6
# Get Customer Usage
# ============================================================

def get_customer_usage(cust_id: str):
    """
    Get all usage information for a customer.
    """

    try:

        # ----------------------------------------------------
        # Find the document containing the customer's
        # usage record inside usage_records array
        # ----------------------------------------------------

        document = db["telecom_usage"].find_one(
            {
                "usage_records": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "usage_records": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No usage information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get all usage records for this customer
        # ----------------------------------------------------

        customer_usage = [
            usage
            for usage in document.get("usage_records", [])
            if usage.get("cust_id") == cust_id
        ]

        # ----------------------------------------------------
        # No usage records
        # ----------------------------------------------------

        if not customer_usage:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No usage information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Sort usage records newest → oldest
        # ----------------------------------------------------

        customer_usage.sort(
            key=lambda usage: usage.get("billing_period", ""),
            reverse=True
        )

        # ----------------------------------------------------
        # Return usage information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer usage information retrieved successfully",
            "total_records": len(customer_usage),
            "data": customer_usage
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer usage information",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 7
# Get Customer VAS
# ============================================================

def get_customer_vas(cust_id: str):
    """
    Get all Value Added Services (VAS) subscribed by a customer.
    """

    try:

        # ----------------------------------------------------
        # Find document containing customer's VAS records
        # ----------------------------------------------------

        document = db["telecom_vas_subscription"].find_one(
            {
                "vas_subscriptions": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "vas_subscriptions": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No VAS information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get customer's VAS records
        # ----------------------------------------------------

        customer_vas = [
            vas
            for vas in document.get("vas_subscriptions", [])
            if vas.get("cust_id") == cust_id
        ]

        # ----------------------------------------------------
        # No VAS records
        # ----------------------------------------------------

        if not customer_vas:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No VAS information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return VAS information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer VAS information retrieved successfully",
            "total_vas": len(customer_vas),
            "data": customer_vas
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer VAS information",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 8
# Get Customer Autopay
# ============================================================

def get_customer_autopay(cust_id: str):
    """
    Get autopay information for a customer.
    """

    try:

        # ----------------------------------------------------
        # Find document containing customer's autopay records
        # ----------------------------------------------------

        document = db["telecom_autopay"].find_one(
            {
                "autopay_records": {
                    "$elemMatch": {
                        "cust_id": cust_id
                    }
                }
            },
            {
                "_id": 0,
                "autopay_records": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No autopay information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Get customer's autopay records
        # ----------------------------------------------------

        customer_autopay = [
            record
            for record in document.get("autopay_records", [])
            if record.get("cust_id") == cust_id
        ]

        # ----------------------------------------------------
        # No autopay records
        # ----------------------------------------------------

        if not customer_autopay:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No autopay information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return autopay information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer autopay information retrieved successfully",
            "total_records": len(customer_autopay),
            "data": customer_autopay
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer autopay information",
            "error": str(e)
        }
# ============================================================
# CUSTOMER TOOL 8
# Get Customer Autopay
# ============================================================

def get_customer_autopay(cust_id: str):
    """
    Get autopay information for a customer.
    """

    try:

        # ----------------------------------------------------
        # Find the document containing autopay records
        # for the given customer
        # ----------------------------------------------------

        document = db["telecom_autopay"].find_one(
            {
                "autopay_records.cust_id": cust_id
            },
            {
                "_id": 0,
                "autopay_records": 1
            }
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if document is None:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No autopay information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Extract customer's autopay records
        # ----------------------------------------------------

        customer_autopay = [
            record
            for record in document.get("autopay_records", [])
            if record.get("cust_id") == cust_id
        ]

        # ----------------------------------------------------
        # No matching records
        # ----------------------------------------------------

        if not customer_autopay:
            return {
                "success": False,
                "customer_id": cust_id,
                "message": f"No autopay information found for customer {cust_id}"
            }

        # ----------------------------------------------------
        # Return autopay information
        # ----------------------------------------------------

        return {
            "success": True,
            "customer_id": cust_id,
            "message": "Customer autopay information retrieved successfully",
            "total_records": len(customer_autopay),
            "data": customer_autopay
        }

    except Exception as e:

        return {
            "success": False,
            "customer_id": cust_id,
            "message": "Failed to retrieve customer autopay information",
            "error": str(e)
        }
# ============================================================
# TEMPORARY TEST CODE
# Get Customer Autopay
# Delete after testing
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Customer ID to test
    # --------------------------------------------------------

    customer_id = "C129"

    print("\n========== TESTING CUSTOMER AUTOPAY ==========")
    print("Testing customer ID:", customer_id)

    # --------------------------------------------------------
    # Call Customer Autopay function
    # --------------------------------------------------------

    result = get_customer_autopay(customer_id)

    # --------------------------------------------------------
    # Display result
    # --------------------------------------------------------

    print("\nSuccess:", result.get("success"))
    print("Customer ID:", result.get("customer_id"))
    print("Message:", result.get("message"))

    # --------------------------------------------------------
    # If successful, display autopay records
    # --------------------------------------------------------

    if result.get("success"):

        print("Total Records:", result.get("total_records"))

        print("\n========== CUSTOMER AUTOPAY ==========")

        for index, record in enumerate(result.get("data", []), start=1):

            print(f"\nAutopay Record {index}:")

            for key, value in record.items():
                print(f"{key}: {value}")

    # --------------------------------------------------------
    # If failed, display error
    # --------------------------------------------------------

    else:

        print("\nError:", result.get("error"))
