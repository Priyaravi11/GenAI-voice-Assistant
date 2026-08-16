from pathlib import Path


# ---------------------------------------------------------
# Document category configuration
# ---------------------------------------------------------

DOCUMENT_CATEGORIES = {
    "billing_upi_policy": {
        "category": "billing",
        "subcategory": "upi",
    },

    "refund_policy": {
        "category": "refund",
        "subcategory": "general",
    },

    "recharge_policy": {
        "category": "recharge",
        "subcategory": "general",
    },

    "network_issue_policy": {
        "category": "network",
        "subcategory": "network_issue",
    },

    "mobile_plan_policy": {
        "category": "plans",
        "subcategory": "mobile_plan",
    },

    "account_policy": {
        "category": "account",
        "subcategory": "account_management",
    },

    "sim_replacement_policy": {
        "category": "sim",
        "subcategory": "sim_replacement",
    },

    "complaint_policy": {
        "category": "complaint",
        "subcategory": "general",
    },
}


def extract_document_metadata(document):
    """
    Extract metadata from a loaded/cleaned document.
    """

    document_id = document["document_id"]

    category_info = DOCUMENT_CATEGORIES.get(
        document_id,
        {
            "category": "general",
            "subcategory": "general",
        }
    )

    metadata = {
        "document_id": document_id,
        "source": document["source"],
        "file_type": document["file_type"],
        "language": document["language"],
        "category": category_info["category"],
        "subcategory": category_info["subcategory"],
    }

    return metadata