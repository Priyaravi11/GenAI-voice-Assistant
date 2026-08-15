from rag.vector_store.retriever import Retriever


# ---------------------------------------------------------
# Retrieval evaluation dataset
# ---------------------------------------------------------

TEST_CASES = [

    # -----------------------------------------------------
    # BILLING
    # -----------------------------------------------------

    {
        "query": "I made a UPI payment but my money was deducted.",
        "expected_document": "billing_upi_policy"
    },

    {
        "query": "My UPI transaction failed after the amount was debited.",
        "expected_document": "billing_upi_policy"
    },

    {
        "query": "I paid using UPI and the payment did not complete.",
        "expected_document": "billing_upi_policy"
    },

    # -----------------------------------------------------
    # REFUND
    # -----------------------------------------------------

    {
        "query": "How long will it take to receive my refund?",
        "expected_document": "refund_policy"
    },

    {
        "query": "When should I expect the money to be returned?",
        "expected_document": "refund_policy"
    },

    # -----------------------------------------------------
    # RECHARGE
    # -----------------------------------------------------

    {
        "query": "My recharge amount was deducted but the recharge is not showing.",
        "expected_document": "recharge_policy"
    },

    {
        "query": "I recharged my phone but the balance was not updated.",
        "expected_document": "recharge_policy"
    },

    # -----------------------------------------------------
    # NETWORK
    # -----------------------------------------------------

    {
        "query": "The mobile signal is very poor where I live.",
        "expected_document": "network_issue_policy"
    },

    {
        "query": "I am having network problems on my phone.",
        "expected_document": "network_issue_policy"
    },

    {
        "query": "My mobile network is not working properly.",
        "expected_document": "network_issue_policy"
    },

    # -----------------------------------------------------
    # MOBILE PLAN
    # -----------------------------------------------------

    {
        "query": "How can I check my current mobile plan?",
        "expected_document": "mobile_plan_policy"
    },

    {
        "query": "What benefits are included in my plan?",
        "expected_document": "mobile_plan_policy"
    },

    # -----------------------------------------------------
    # ACCOUNT
    # -----------------------------------------------------

    {
        "query": "I think someone has accessed my account.",
        "expected_document": "account_policy"
    },

    {
        "query": "What should I do if I notice suspicious activity on my account?",
        "expected_document": "account_policy"
    },

    # -----------------------------------------------------
    # SIM
    # -----------------------------------------------------

    {
        "query": "My SIM card is damaged. How can I replace it?",
        "expected_document": "sim_replacement_policy"
    },

    {
        "query": "I lost my SIM. How can I get a replacement?",
        "expected_document": "sim_replacement_policy"
    },

    # -----------------------------------------------------
    # COMPLAINT
    # -----------------------------------------------------

    {
        "query": "I want to raise a complaint about an unresolved issue.",
        "expected_document": "complaint_policy"
    },

    {
        "query": "How can I register a customer service complaint?",
        "expected_document": "complaint_policy"
    },

    # -----------------------------------------------------
    # UNRELATED
    # -----------------------------------------------------

    {
        "query": "What is the weather today?",
        "expected_document": None
    },

    {
        "query": "Who won the cricket match yesterday?",
        "expected_document": None
    },
]


def test_retrieval_accuracy():

    retriever = Retriever(
        top_k=3,
        score_threshold=0.50
    )

    passed = 0
    failed = 0

    print("\n")
    print("=" * 70)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 70)

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        query = test_case["query"]
        expected = test_case["expected_document"]

        results = retriever.search(query)

        # -------------------------------------------------
        # Case 1: Expected NO result
        # -------------------------------------------------

        if expected is None:

            if not results:

                print(
                    f"\n[{index}] PASS"
                )

                print(
                    f"Query: {query}"
                )

                print(
                    "Expected: No relevant document"
                )

                passed += 1

            else:

                print(
                    f"\n[{index}] FAIL"
                )

                print(
                    f"Query: {query}"
                )

                print(
                    "Expected: No relevant document"
                )

                print(
                    f"Got: {results[0]['metadata']['document_id']}"
                )

                failed += 1

            continue

        # -------------------------------------------------
        # Case 2: Expected document
        # -------------------------------------------------

        if results:

            top_result = results[0]

            actual = top_result[
                "metadata"
            ][
                "document_id"
            ]

            score = top_result[
                "relevance_score"
            ]

        else:

            actual = None
            score = 0.0

        # -------------------------------------------------
        # Check result
        # -------------------------------------------------

        if actual == expected:

            print(
                f"\n[{index}] PASS"
            )

            print(
                f"Query: {query}"
            )

            print(
                f"Expected: {expected}"
            )

            print(
                f"Retrieved: {actual}"
            )

            print(
                f"Score: {score}"
            )

            passed += 1

        else:

            print(
                f"\n[{index}] FAIL"
            )

            print(
                f"Query: {query}"
            )

            print(
                f"Expected: {expected}"
            )

            print(
                f"Retrieved: {actual}"
            )

            print(
                f"Score: {score}"
            )

            failed += 1

    # -----------------------------------------------------
    # Final summary
    # -----------------------------------------------------

    total = passed + failed

    accuracy = (
        passed / total * 100
        if total > 0
        else 0
    )

    print("\n")
    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(
        f"Total tests : {total}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Failed      : {failed}"
    )

    print(
        f"Accuracy    : {accuracy:.2f}%"
    )

    print("=" * 70)

    assert accuracy >= 70.0, (
        f"Retrieval accuracy is too low: "
        f"{accuracy:.2f}%"
    )