from context.context_builder import ContextBuilder


def test_context_builder():

    builder = ContextBuilder(
        max_context_documents=3
    )

    customer_context = {
        "language": "ta",
        "code_switched": True,
        "intent": "billing_issue",
        "entities": {
            "amount": "599",
            "payment_method": "UPI",
            "date": "yesterday"
        },
        "sentiment": "negative"
    }

    retrieved_context = [
        {
            "chunk_id": "chunk_1",

            "content": "UPI payment refund policy.",

            "relevance_score": 0.89,

            "metadata": {
                "source": "billing_upi_policy.docx",
                "language": "en",
                "category": "billing"
            }
        }
    ]

    response_requirements = {
        "language": "ta",
        "use_context_only": True,
        "do_not_invent_information": True
    }

    result = builder.build(
        request_id="REQ001",

        customer_context=customer_context,

        customer_query=(
            "I made a UPI payment yesterday "
            "and 599 rupees was deducted."
        ),

        retrieved_context=retrieved_context,

        response_requirements=response_requirements
    )

    print("\n")
    print("=" * 70)
    print("CONTEXT BUILDER TEST")
    print("=" * 70)

    print(result)

    print("=" * 70)

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    assert result["request_id"] == "REQ001"

    assert (
        result["customer_context"]["intent"]
        == "billing_issue"
    )

    assert (
        result["customer_query"]
        == "I made a UPI payment yesterday "
           "and 599 rupees was deducted."
    )

    assert len(
        result["retrieved_context"]
    ) == 1

    assert (
        result["retrieved_context"][0]["source"]
        == "billing_upi_policy.docx"
    )

    assert (
        result["retrieved_context"][0]["language"]
        == "en"
    )

    assert (
        result["response_requirements"]["language"]
        == "ta"
    )

    assert (
        result["response_requirements"]["use_context_only"]
        is True
    )

    assert (
        result["response_requirements"]
        ["do_not_invent_information"]
        is True
    )

    print("\nCONTEXT BUILDER TEST PASSED!")