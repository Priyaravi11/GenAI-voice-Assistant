import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load .env from project root
env_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../.env"
    )
)

load_dotenv(env_path)

# Read MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# Create MongoDB client
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

# Select database
db = client[MONGODB_DATABASE]

# Test connection
client.admin.command("ping")

print("MongoDB connected successfully!")
print("Database:", MONGODB_DATABASE)
# Billing collection
billing_collection = db["telecom_billing_history"]

print("Billing collection connected:", billing_collection.name)