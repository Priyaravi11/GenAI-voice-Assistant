"""
Real RAG integration test.

This test uses the actual RAG pipeline:

    QueryProcessor
        ↓
    Retriever
        ↓
    EmbeddingModel
        ↓
    ChromaDB
        ↓
    ContextBuilder
"""


from rag.query.query_processor import QueryProcessor


def test_real_rag_retrieval():
    """
    Test the complete RAG pipeline using the
    actual knowledge base and vector store.
    """

    # ---------------------------------------------------------
    # Create the real QueryProcessor
    # ---------------------------------------------------------

    processor = QueryProcessor(
        top_k=3,
        score_threshold=0.50,
    )

    # ---------------------------------------------------------
    # Example NLU output
    # ---------------------------------------------------------

    nlu_data = {
        "request_id": "TEST-RAG-001",

        "language": {
            "primary": "en",
            "code_switched": False,
        },

        "intent": {
            "name": "billing",
        },

        "entities": {},

        "sentiment": {
            "label": "neutral",
        },

        "customer_query": (
            "Why is my bill higher this month?"
        ),
    }

    # ---------------------------------------------------------
    # Run the actual RAG pipeline
    # ---------------------------------------------------------

    result = processor.process(
        nlu_data
    )

    # ---------------------------------------------------------
    # Basic checks
    # ---------------------------------------------------------

    assert result is not None

    assert result["request_id"] == (
        "TEST-RAG-001"
    )

    assert result["customer_query"] == (
        "Why is my bill higher this month?"
    )

    # ---------------------------------------------------------
    # Check retrieved context
    # ---------------------------------------------------------

    assert "retrieved_context" in result

    retrieved_context = result[
        "retrieved_context"
    ]

    print("\n================================")
    print("REAL RAG RETRIEVAL RESULT")
    print("================================")

    print(
        f"Documents retrieved: "
        f"{len(retrieved_context)}"
    )

    for index, document in enumerate(
        retrieved_context,
        start=1,
    ):
        print(
            f"\n--- Document {index} ---"
        )

        print(
            "Content:",
            document.get("content"),
        )

        print(
            "Score:",
            document.get("relevance_score"),
        )

        print(
            "Source:",
            document.get("source"),
        )

        print(
            "Language:",
            document.get("language"),
        )

    # ---------------------------------------------------------
    # We expect at least one relevant document
    # ---------------------------------------------------------

    assert len(retrieved_context) > 0

    # ---------------------------------------------------------
    # Check document structure
    # ---------------------------------------------------------

    first_document = retrieved_context[0]

    assert "content" in first_document
    assert "relevance_score" in first_document
    assert "source" in first_document
    assert "language" in first_document

    # ---------------------------------------------------------
    # Check response requirements
    # ---------------------------------------------------------

    assert (
        result["response_requirements"]
        ["use_context_only"]
        is True
    )

    assert (
        result["response_requirements"]
        ["do_not_invent_information"]
        is True
    )

    print(
        "\n✅ REAL RAG TEST PASSED"
    )