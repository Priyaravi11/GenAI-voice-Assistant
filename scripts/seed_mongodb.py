"""
MongoDB seed script for GenAI Voice Assistant.

Populates MongoDB with initial test data including:
- Customer profiles
- Call records
- Billing information
- Agent profiles
- Escalation cases

Usage:
    python scripts/seed_mongodb.py              # Seed all data
    python scripts/seed_mongodb.py --dry-run    # Show what would be inserted
    python scripts/seed_mongodb.py --clear      # Clear collections first
    python scripts/seed_mongodb.py --customers-only  # Seed only customers
"""

import os
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}[PASS] {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}[FAIL] {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")


def get_sample_customers() -> List[Dict[str, Any]]:
    """Get sample customer data."""
    return [
        {
            "customer_id": "C001",
            "name": "Rajesh Kumar",
            "email": "rajesh.kumar@example.com",
            "phone": "9876543210",
            "account_type": "premium",
            "status": "active",
            "created_at": datetime.now(),
            "language_preference": "en",
        },
        {
            "customer_id": "C002",
            "name": "Priya Sharma",
            "email": "priya.sharma@example.com",
            "phone": "9876543211",
            "account_type": "standard",
            "status": "active",
            "created_at": datetime.now(),
            "language_preference": "hi",
        },
        {
            "customer_id": "C003",
            "name": "Arjun Patel",
            "email": "arjun.patel@example.com",
            "phone": "9876543212",
            "account_type": "premium",
            "status": "active",
            "created_at": datetime.now(),
            "language_preference": "en",
        },
        {
            "customer_id": "C004",
            "name": "Anjali Singh",
            "email": "anjali.singh@example.com",
            "phone": "9876543213",
            "account_type": "standard",
            "status": "active",
            "created_at": datetime.now(),
            "language_preference": "ta",
        },
    ]


def get_sample_billing() -> List[Dict[str, Any]]:
    """Get sample billing data."""
    return [
        {
            "customer_id": "C001",
            "bill_id": "B001",
            "month": "2026-08",
            "amount": 1500.00,
            "due_date": "2026-09-16",
            "status": "pending",
            "charges": [
                {"description": "Monthly Plan", "amount": 999.00},
                {"description": "International Roaming", "amount": 501.00},
            ],
            "created_at": datetime.now(),
        },
        {
            "customer_id": "C002",
            "bill_id": "B002",
            "month": "2026-08",
            "amount": 1200.00,
            "due_date": "2026-09-16",
            "status": "paid",
            "charges": [
                {"description": "Monthly Plan", "amount": 799.00},
                {"description": "Data Addon", "amount": 401.00},
            ],
            "created_at": datetime.now(),
        },
        {
            "customer_id": "C003",
            "bill_id": "B003",
            "month": "2026-08",
            "amount": 1800.00,
            "due_date": "2026-09-16",
            "status": "pending",
            "charges": [
                {"description": "Premium Plan", "amount": 1299.00},
                {"description": "Additional Services", "amount": 501.00},
            ],
            "created_at": datetime.now(),
        },
    ]


def get_sample_calls() -> List[Dict[str, Any]]:
    """Get sample call records."""
    return [
        {
            "call_id": "CALL001",
            "customer_id": "C001",
            "start_time": datetime.now() - timedelta(hours=2),
            "end_time": datetime.now() - timedelta(hours=2, minutes=-5),
            "duration": 300,
            "transcript": "Customer inquired about billing charges and payment options.",
            "agent_type": "ai",
            "status": "completed",
            "language": "en",
            "intent": "billing_inquiry",
        },
        {
            "call_id": "CALL002",
            "customer_id": "C002",
            "start_time": datetime.now() - timedelta(hours=1),
            "end_time": datetime.now() - timedelta(hours=1, minutes=-8),
            "duration": 480,
            "transcript": "Customer requested plan upgrade to premium.",
            "agent_type": "human",
            "status": "completed",
            "language": "hi",
            "intent": "plan_upgrade",
        },
        {
            "call_id": "CALL003",
            "customer_id": "C003",
            "start_time": datetime.now() - timedelta(minutes=30),
            "end_time": datetime.now() - timedelta(minutes=25),
            "duration": 300,
            "transcript": "Customer reported network issues and outage.",
            "agent_type": "ai",
            "status": "escalated",
            "language": "en",
            "intent": "technical_support",
        },
    ]


def get_sample_agents() -> List[Dict[str, Any]]:
    """Get sample agent profiles."""
    return [
        {
            "agent_id": "A001",
            "name": "Amit Verma",
            "email": "amit@company.com",
            "role": "support_specialist",
            "status": "active",
            "availability": "online",
            "queue_size": 3,
        },
        {
            "agent_id": "A002",
            "name": "Neha Gupta",
            "email": "neha@company.com",
            "role": "senior_specialist",
            "status": "active",
            "availability": "online",
            "queue_size": 1,
        },
        {
            "agent_id": "A003",
            "name": "Vikram Reddy",
            "email": "vikram@company.com",
            "role": "technical_specialist",
            "status": "active",
            "availability": "offline",
            "queue_size": 0,
        },
    ]


def get_sample_escalations() -> List[Dict[str, Any]]:
    """Get sample escalation cases."""
    return [
        {
            "case_id": "ESC001",
            "customer_id": "C001",
            "call_id": "CALL001",
            "reason": "customer_request",
            "priority": "high",
            "status": "assigned",
            "assigned_agent": "A001",
            "created_at": datetime.now() - timedelta(hours=1),
            "resolved_at": None,
        },
        {
            "case_id": "ESC002",
            "customer_id": "C003",
            "call_id": "CALL003",
            "reason": "repeated_failures",
            "priority": "urgent",
            "status": "in_progress",
            "assigned_agent": "A003",
            "created_at": datetime.now() - timedelta(minutes=30),
            "resolved_at": None,
        },
    ]


def connect_mongodb(connection_string: Optional[str] = None):
    """Connect to MongoDB using pymongo."""
    from pymongo import MongoClient
    uri = connection_string or os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/telecom_db")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print_success("Connected to local MongoDB successfully.")
        return client
    except Exception as e:
        print_error(f"Failed to connect to MongoDB: {str(e)}")
        return None


def clear_collections(db: Any, collections: List[str]) -> None:
    """Clear specified collections."""
    for collection_name in collections:
        try:
            db[collection_name].delete_many({})
            print_success(f"Cleared collection: {collection_name}")
        except Exception as e:
            print_error(f"Failed to clear {collection_name}: {e}")


def insert_data(db: Any, collection_name: str, data: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """Insert data into collection."""
    if dry_run:
        print_info(f"[DRY RUN] Would insert {len(data)} documents into {collection_name}")
        return len(data)
    try:
        result = db[collection_name].insert_many(data)
        count = len(result.inserted_ids)
        print_success(f"Inserted {count} documents into {collection_name}")
        return count
    except Exception as e:
        print_error(f"Failed to insert into {collection_name}: {e}")
        return 0


def seed_database(
    connection_string: Optional[str] = None,
    dry_run: bool = False,
    clear: bool = False,
    customers_only: bool = False,
    agents_only: bool = False,
) -> bool:
    """Main seed function."""
    print(f"\n{'='*60}")
    print("MongoDB Seed Script")
    print(f"{'='*60}\n")
    
    client = connect_mongodb(connection_string)
    if not client:
        return False
    
    try:
        db_name = os.getenv("MONGODB_DATABASE", "telecom_db")
        db = client[db_name]
        
        if clear:
            print_info("Clearing existing data...")
            clear_collections(db, ["customers", "billing", "calls", "agents", "escalations"])
        
        total_inserts = 0
        if customers_only or not agents_only:
            print_info("Seeding customers...")
            total_inserts += insert_data(db, "customers", get_sample_customers(), dry_run)
        
        if not customers_only and not agents_only:
            print_info("Seeding billing data...")
            total_inserts += insert_data(db, "billing", get_sample_billing(), dry_run)
            
            print_info("Seeding call records...")
            total_inserts += insert_data(db, "calls", get_sample_calls(), dry_run)
            
            print_info("Seeding escalation cases...")
            total_inserts += insert_data(db, "escalations", get_sample_escalations(), dry_run)
        
        if agents_only or not customers_only:
            print_info("Seeding agent profiles...")
            total_inserts += insert_data(db, "agents", get_sample_agents(), dry_run)
        
        print(f"\n{'='*60}")
        print(f"Successfully inserted {total_inserts} documents")
        print(f"{'='*60}\n")
        return True
    
    except Exception as e:
        print_error(f"Seeding failed: {e}")
        return False
    finally:
        client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed MongoDB with test data")
    parser.add_argument(
        "--mongodb-uri",
        help="MongoDB connection string (default: mongodb://localhost:27017)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be inserted without inserting"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear collections before seeding"
    )
    parser.add_argument(
        "--customers-only",
        action="store_true",
        help="Seed only customer data"
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Seed only agent profiles"
    )
    
    args = parser.parse_args()
    
    # Run seeding
    success = seed_database(
        connection_string=args.mongodb_uri,
        dry_run=args.dry_run,
        clear=args.clear,
        customers_only=args.customers_only,
        agents_only=args.agents_only,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
