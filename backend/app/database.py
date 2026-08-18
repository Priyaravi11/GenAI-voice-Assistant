import logging
import os
from dotenv import load_dotenv
from pymongo import MongoClient

logger = logging.getLogger(__name__)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# .env is located in the project root
env_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../.env"
    )
)

load_dotenv(env_path)


# ============================================================
# MONGODB CONFIGURATION
# ============================================================

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")


# ============================================================
# VALIDATE MONGODB CONFIGURATION
# ============================================================

if not MONGODB_URI:
    raise ValueError(
        "MONGODB_URI is not set in the .env file"
    )

if not MONGODB_DATABASE:
    raise ValueError(
        "MONGODB_DATABASE is not set in the .env file"
    )


# ============================================================
# CREATE MONGODB CLIENT
# ============================================================

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
    connect=False,
)


# ============================================================
# SELECT DATABASE
# ============================================================

db = client[MONGODB_DATABASE]


# ============================================================
# MONGODB CONNECTION CHECK
# ============================================================

DB_CONNECTED = False


def check_connection() -> bool:
    """
    Ping MongoDB on demand without making app imports depend on the network.
    """

    global DB_CONNECTED

    try:
        client.admin.command("ping")
        DB_CONNECTED = True
        return True

    except Exception as e:
        logger.warning(
            f"MongoDB connection warning: {e}. "
            "Some features will not work until MongoDB is available."
        )
        DB_CONNECTED = False
        return False

# ============================================================
# COLLECTIONS
# ============================================================

# ------------------------------------------------------------
# BILLING
# ------------------------------------------------------------

billing_collection = db["telecom_billing_history"]

billing_preferences_collection = db[
    "telecom_billing_preferences"
]

billing_queries_collection = db[
    "telecom_billing_querries"
]


# ------------------------------------------------------------
# COMPLAINT
# ------------------------------------------------------------

complaint_collection = db[
    "telecom_complaint"
]


# ------------------------------------------------------------
# NETWORK
# ------------------------------------------------------------

network_collection = db[
    "telecom_network"
]


# ------------------------------------------------------------
# PAYMENTS
# ------------------------------------------------------------

payments_collection = db[
    "telecom_payments"
]


# ------------------------------------------------------------
# PLANS
# ------------------------------------------------------------

plans_collection = db[
    "telecom_plans"
]


# ------------------------------------------------------------
# RECHARGES
# ------------------------------------------------------------

recharges_collection = db[
    "telecom_recharges"
]


# ------------------------------------------------------------
# REFUNDS
# ------------------------------------------------------------

refunds_collection = db[
    "telecom_refunds"
]


# ------------------------------------------------------------
# SERVICE
# ------------------------------------------------------------

service_collection = db[
    "telecom_service"
]


# ------------------------------------------------------------
# TAX CHARGES
# ------------------------------------------------------------

tax_charges_collection = db[
    "telecom_tax_charges"
]


# ------------------------------------------------------------
# USAGE
# ------------------------------------------------------------

usage_collection = db[
    "telecom_usage"
]


# ------------------------------------------------------------
# VAS SUBSCRIPTION
# ------------------------------------------------------------

vas_subscription_collection = db[
    "telecom_vas_subscription"
]


# ============================================================
# OPTIONAL: LIST ALL COLLECTIONS
# ============================================================

ALL_COLLECTIONS = {
    "billing": billing_collection,
    "billing_preferences": billing_preferences_collection,
    "billing_queries": billing_queries_collection,
    "complaint": complaint_collection,
    "network": network_collection,
    "payments": payments_collection,
    "plans": plans_collection,
    "recharges": recharges_collection,
    "refunds": refunds_collection,
    "service": service_collection,
    "tax_charges": tax_charges_collection,
    "usage": usage_collection,
    "vas_subscription": vas_subscription_collection,
}
