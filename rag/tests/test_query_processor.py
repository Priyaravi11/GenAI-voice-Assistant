from rag.query.query_processor import QueryProcessor
from pprint import pprint


def test_nlu_to_rag_with_metadata_filter():

    # -------------------------------------------------
    # NLU OUTPUT
    # -------------------------------------------------

    nlu_data = {
        "request_id": "REQ001",

        "language": {
            "primary": "ta",
            "code_switched": True,
            "confidence": 0.96
        },

        "intent": {
            "name": "billing_issue",
            "confidence": 0.94
        },

        "entities": {
            "account_number": None,
            "phone_number": None,
            "amount": "599",
            "plan": None,
            "payment_method": "UPI",
            "transaction_id": None,
            "date": "yesterday",
            "location": None,
            "service": None
        },

        "sentiment": {
            "label": "negative",
            "confidence": 0.91
        },

        # IMPORTANT:
        # This is the English transcript coming from
        # ASR + NLU layer.
        "customer_query":
            "I made a UPI payment yesterday and 599 rupees was deducted."
    }

    # -------------------------------------------------
    # CREATE QUERY PROCESSOR
    # -------------------------------------------------

    processor = QueryProcessor(
        top_k=3
    )

    # -------------------------------------------------
    # PROCESS NLU → RAG
    # -------------------------------------------------

    result = processor.process(
        nlu_data
    )

    # -------------------------------------------------
    # DISPLAY RESULT
    # -------------------------------------------------

    print("\n")
    print("=" * 70)
    print("STEP 25 - COMPLETE NLU → RAG TEST")
    print("=" * 70)

    pprint(result)

    print("=" * 70)

    # -------------------------------------------------
    # BASIC VALIDATION
    # -------------------------------------------------

    assert result["request_id"] == "REQ001"

    assert result["customer_context"]["language"] == "ta"

    assert result["customer_context"]["intent"] == "billing_issue"

    assert result["customer_context"]["sentiment"] == "negative"

    assert (
        result["customer_query"]
        == "I made a UPI payment yesterday and 599 rupees was deducted."
    )

    # -------------------------------------------------
    # RETRIEVAL VALIDATION
    # -------------------------------------------------

    assert len(
        result["retrieved_context"]
    ) > 0

    # -------------------------------------------------
    # METADATA FILTER VALIDATION
    # -------------------------------------------------

    for document in result["retrieved_context"]:

        assert document["language"] == "en"

        assert document["source"] is not None

    # -------------------------------------------------
    # RESPONSE REQUIREMENTS
    # -------------------------------------------------

    assert (
        result["response_requirements"]["language"]
        == "ta"
    )

    assert (
        result["response_requirements"]["use_context_only"]
        is True
    )

    assert (
        result["response_requirements"]["do_not_invent_information"]
        is True
    )

    print("\nSTEP 25 TEST PASSED!")