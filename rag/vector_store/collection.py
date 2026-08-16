from rag.vector_store.client import get_chroma_client


COLLECTION_NAME = "customer_care_knowledge"


def get_collection():
    """
    Create or retrieve the customer-care knowledge collection.
    """

    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={
            "hnsw": {
                "space": "cosine"
            }
        }
    )

    return collection