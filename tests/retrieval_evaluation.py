from rag.vector_store.retriever import Retriever


TEST_CASES = [
    # -------------------------
    # BILLING
    # -------------------------
    {
        "query": "Why was I charged extra for data?",
        "expected_category": "billing",
    },
    {
        "query": "Why is my bill incorrect?",
        "expected_category": "billing",
    },
    {
        "query": "I was charged twice for the same payment",
        "expected_category": "billing",
    },

    # -------------------------
    # PLANS
    # -------------------------
    {
        "query": "How can I upgrade my plan?",
        "expected_category": "plans",
    },
    {
        "query": "Can I change my mobile plan?",
        "expected_category": "plans",
    },
    {
        "query": "Can I buy another plan?",
        "expected_category": "plans",
    },

    # -------------------------
    # TECHNICAL
    # -------------------------
    {
        "query": "My internet is not working",
        "expected_category": "technical",
    },
    {
        "query": "My network connection is unstable",
        "expected_category": "technical",
    },

    # -------------------------
    # NO ANSWER / OUT OF DOMAIN
    # -------------------------
    {
        "query": "How do I change my home address?",
        "expected_category": None,
    },
    {
        "query": "What is the weather today?",
        "expected_category": None,
    },
    {
        "query": "How do I book a flight?",
        "expected_category": None,
    },
]


def evaluate():

    retriever = Retriever(
        top_k=3,
        score_threshold=0.60
    )

    total = len(TEST_CASES)
    correct = 0

    print("\n")
    print("=" * 80)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 80)

    for index, test in enumerate(TEST_CASES, start=1):

        query = test["query"]
        expected_category = test["expected_category"]

        results = retriever.search(query)

        print("\n" + "-" * 80)
        print(f"TEST {index}/{total}")
        print("Query:", query)
        print("Expected:", expected_category)

        if not results:
            predicted_category = None
            best_score = 0.0
        else:
            predicted_category = results[0]["metadata"].get("category")
            best_score = results[0]["relevance_score"]

        print("Predicted:", predicted_category)
        print("Best score:", best_score)

        # ---------------------------------
        # Evaluation
        # ---------------------------------

        if expected_category is None:

            # For an out-of-domain query,
            # retrieval should ideally return nothing.
            if not results:
                correct += 1
                print("RESULT: PASS")
            else:
                print("RESULT: FAIL - irrelevant documents retrieved")

        else:

            if predicted_category == expected_category:
                correct += 1
                print("RESULT: PASS")
            else:
                print("RESULT: FAIL")

    # -------------------------------------
    # Final statistics
    # -------------------------------------

    accuracy = (correct / total) * 100

    print("\n")
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    print(f"Total tests : {total}")
    print(f"Correct     : {correct}")
    print(f"Accuracy    : {accuracy:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    evaluate()