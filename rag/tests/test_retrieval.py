from rag.vector_store.retriever import Retriever


def test_retrieval():

    retriever = Retriever(
        top_k=3,
        score_threshold=0.50
    )

    test_cases = [
        {
            "query": "Why was I charged extra for data?",
            "category": "billing"
        },
        {
            "query": "How can I upgrade my plan?",
            "category": "plans"
        },
        {
            "query": "My internet is not working",
            "category": "technical"
        },
        {
            "query": "How do I change my home address?",
            "category": None
        }
    ]

    for test in test_cases:

        metadata_filter = None

        if test["category"]:
            metadata_filter = {
                "category": test["category"]
            }

        print("\n" + "=" * 70)
        print("QUERY:", test["query"])
        print("FILTER:", metadata_filter)

        results = retriever.search(
            query=test["query"],
            metadata_filter=metadata_filter
        )

        print("\nFINAL RESULTS:")

        if not results:
            print("No relevant documents found.")

        for result in results:
            print("\nContent:", result["content"])
            print("Score:", result["relevance_score"])
            print("Metadata:", result["metadata"])


if __name__ == "__main__":
    test_retrieval()