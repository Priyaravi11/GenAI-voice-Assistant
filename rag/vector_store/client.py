import os
import chromadb
from pathlib import Path


# ============================================================
# Project Paths
# ============================================================

# client.py location:
# project/
# └── rag/
#     └── vector_store/
#         └── client.py
#
# parents[2] gives the project root.

PROJECT_ROOT = Path(__file__).resolve().parents[2]

configured_chroma_path = Path(
    os.getenv("CHROMA_PATH", "rag/data/chroma")
)

CHROMA_PATH = (
    configured_chroma_path
    if configured_chroma_path.is_absolute()
    else PROJECT_ROOT / configured_chroma_path
)


# ============================================================
# ChromaDB Client
# ============================================================

def get_chroma_client():
    """
    Create and return a persistent ChromaDB client.

    ChromaDB data is stored inside:

        rag/data/chroma/

    This uses an absolute path so the application works
    correctly regardless of the directory from which
    Python is executed.
    """

    CHROMA_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    return client
