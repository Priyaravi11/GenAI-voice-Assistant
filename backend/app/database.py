import os
from dotenv import load_dotenv
from pymongo import MongoClient


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
    serverSelectionTimeoutMS=5000
)


# ============================================================
# SELECT DATABASE
# ============================================================

db = client[MONGODB_DATABASE]


# ============================================================
# TEST MONGODB CONNECTION
# ============================================================

client.admin.command("ping")


# ============================================================
# COLLECTIONS
# ============================================================

# Billing history
billing_collection = db["telecom_billing_history"]

# Telecom plans
plans_collection = db["telecom_plans"]