from rag.embeddings.embedding_model import EmbeddingModel
from rag.vector_store.collection import get_collection


class Retriever:
    """
    Retrieves the most relevant knowledge-base chunks
    for an English customer query.

    Supports optional metadata filtering using ChromaDB.
    """

    def __init__(self, top_k=3, score_threshold=0.50):
        self.collection = get_collection()
        self.embedding_model = EmbeddingModel()
        self.top_k = top_k
        self.score_threshold = score_threshold

    def search(self, query: str, metadata_filter=None):
        """
        Search ChromaDB using semantic similarity.

        Args:
            query (str):
                English customer query.

            metadata_filter (dict, optional):
                ChromaDB metadata filter.

        Returns:
            list:
                Retrieved knowledge-base chunks.
        """

        # -------------------------------------------------
        # STEP 1: Validate query
        # -------------------------------------------------

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        # -------------------------------------------------
        # STEP 2: Generate query embedding
        # -------------------------------------------------

        query_embedding = self.embedding_model.embed_text(
            query
        )

        # -------------------------------------------------
        # STEP 3: Prepare ChromaDB search arguments
        # -------------------------------------------------

        query_arguments = {
            "query_embeddings": [query_embedding],
            "n_results": self.top_k,
            "include": [
                "documents",
                "metadatas",
                "distances"
            ]
        }

        # -------------------------------------------------
        # STEP 4: Add metadata filter if provided
        # -------------------------------------------------

        if metadata_filter:
            query_arguments["where"] = metadata_filter

        # -------------------------------------------------
        # STEP 5: Search ChromaDB
        # -------------------------------------------------

        results = self.collection.query(
            **query_arguments
        )

        # -------------------------------------------------
        # STEP 6: Extract results
        # -------------------------------------------------

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        ids = results.get(
            "ids",
            [[]]
        )[0]

        # -------------------------------------------------
        # STEP 7: Format retrieved context
        # -------------------------------------------------

        retrieved_context = []

        for chunk_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances
        ):

            # ChromaDB cosine distance:
            # similarity = 1 - distance
            relevance_score = 1 - distance

            if relevance_score < self.score_threshold:

              continue

            retrieved_context.append(
                {
                    "chunk_id": chunk_id,
                    "content": document,
                    "relevance_score": round(
                        relevance_score,
                        4
                    ),
                    "metadata": metadata
                }
            )

        # -------------------------------------------------
        # STEP 8: Return results
        # -------------------------------------------------

        return retrieved_context