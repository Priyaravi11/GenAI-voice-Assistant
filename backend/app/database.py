import os
from dotenv import load_dotenv
from pymongo import MongoClient

# ============================================================
# LOAD .ENV
# ============================================================

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


if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in .env")

if not MONGODB_DATABASE:
    raise ValueError("MONGODB_DATABASE is not set in .env")


# ============================================================
# MONGODB CONNECTION
# ============================================================

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

# Test connection
client.admin.command("ping")

# Select database
db = client[MONGODB_DATABASE]

print("MongoDB connected successfully!")
print("Database:", MONGODB_DATABASE)


# ============================================================
# COLLECTIONS
# ============================================================

billing_collection = db["telecom_billing_history"]

payments_collection = db["telecom_payments"]

network_collection = db["telecom_network"]

plans_collection = db["telecom_plans"]

subscriptions_collection = db["telecom_vas_subscription"]

recharges_collection = db["telecom_recharges"]

usage_collection = db["telecom_usage"]

refunds_collection = db["telecom_refunds"]

account_collection = db["telecom_account"]

autopay_collection = db["telecom_autopay"]

billing_preferences_collection = db["telecom_billing_preferences"]

complaint_collection = db["telecom_complaint"]

tax_charges_collection = db["telecom_tax_charges"]

adjustments_collection = db["telecom_adjusments"]

billing_queries_collection = db["telecom_billing_querries"]


# ============================================================
# CONNECTION TEST
# ============================================================

if __name__ == "__main__":

    print("\n========== DATABASE TEST ==========")

    print("Database:", db.name)

    print("\nCollections:")

    for collection in db.list_collection_names():
        print("-", collection)

    print("\nConnection successful!")