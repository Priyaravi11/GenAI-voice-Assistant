import chromadb
from pathlib import Path


CHROMA_PATH = Path("data/chroma")


def get_chroma_client():
    """
    Create and return a persistent ChromaDB client.
    """

    CHROMA_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    return client