from rag.vector_store.collection import get_collection


def index_chunks(chunks, embeddings):
    """
    Store document chunks, embeddings, and metadata in ChromaDB.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must be the same."
        )

    collection = get_collection()

    ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    documents = [
        chunk["text"]
        for chunk in chunks
    ]

    metadatas = [
        chunk["metadata"]
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)