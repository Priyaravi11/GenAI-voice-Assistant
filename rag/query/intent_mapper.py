"""
Maps NLU intent and entities to ChromaDB metadata filters.
"""


INTENT_TO_CATEGORY = {
    "billing_issue": "billing",
    "refund_issue": "refund",
    "recharge_issue": "recharge",
    "network_issue": "network",
    "account_issue": "account",
    "sim_replacement": "sim",
    "sim_issue": "sim",
    "complaint": "complaint",
    "complaint_issue": "complaint",
    "mobile_plan_issue": "plans",
    "plan_issue": "plans",
}


def build_metadata_filter(nlu_data: dict):
    """
    Build a ChromaDB metadata filter from NLU JSON.

    Returns:
        dict | None
    """

    intent = nlu_data.get("intent", {})

    if isinstance(intent, dict):
        intent_name = intent.get("name")
    else:
        intent_name = intent

    entities = nlu_data.get("entities", {})

    if not isinstance(entities, dict):
        entities = {}

    filters = []

    # -------------------------------------------------
    # INTENT → CATEGORY
    # -------------------------------------------------

    category = INTENT_TO_CATEGORY.get(intent_name)

    if category:
        filters.append(
            {
                "category": category
            }
        )

    # -------------------------------------------------
    # PAYMENT METHOD → SUBCATEGORY
    # -------------------------------------------------

    payment_method = entities.get("payment_method")

    if payment_method:
        payment_method = str(payment_method).lower()

        if payment_method == "upi":
            filters.append(
                {
                    "subcategory": "upi"
                }
            )

    # -------------------------------------------------
    # BUILD CHROMA FILTER
    # -------------------------------------------------

    if not filters:
        return None

    if len(filters) == 1:
        return filters[0]

    return {
        "$and": filters
    }