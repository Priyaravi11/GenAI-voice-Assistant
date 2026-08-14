from vector_store.retriever import Retriever
from pprint import pprint


def test_filtered_retrieval():

    retriever = Retriever(top_k=3)

    metadata_filter = {
        "$and": [
            {"category": "billing"},
            {"subcategory": "upi"}
        ]
    }

    results = retriever.search(
        "I made a UPI payment but my money was deducted.",
        metadata_filter=metadata_filter
    )

    pprint(results)

    assert len(results) > 0

    for result in results:
        assert result["metadata"]["category"] == "billing"
        assert result["metadata"]["subcategory"] == "upi"