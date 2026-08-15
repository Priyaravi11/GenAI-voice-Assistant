import chromadb
from sentence_transformers import SentenceTransformer

from rag.retrieval.retriever import Retriever


CHROMA_PATH = "rag/chroma_test_bge"
COLLECTION_NAME = "customer_care_knowledge"


def setup_test_data():

    model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5"
    )

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    documents = [
        "Customers who exceed their monthly data limit may be charged for additional data usage.",

        "Customers can check their current data usage through the customer portal.",

        "Late payment may result in additional charges according to the billing policy.",

        "Customers can upgrade their plan to receive additional monthly data."
    ]

    metadata = [
        {
            "category": "billing",
            "customer_id": "C101"
        },
        {
            "category": "billing",
            "customer_id": "C101"
        },
        {
            "category": "payment",
            "customer_id": "C101"
        },
        {
            "category": "plans",
            "customer_id": "C101"
        }
    ]

    ids = [
        "bge_test_001",
        "bge_test_002",
        "bge_test_003",
        "bge_test_004"
    ]

    embeddings = model.encode(
        documents,
        normalize_embeddings=True
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadata
    )


def test_retrieval():

    setup_test_data()

    retriever = Retriever(
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME
    )

    response = retriever.retrieve(
        query="Why was I charged extra for data?",
        category="billing",
        customer_id="C999",
        top_k=3
    )

    print("\nRAG RESPONSE:")
    print(response)


if __name__ == "__main__":
    test_retrieval()