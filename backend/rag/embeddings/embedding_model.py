from sentence_transformers import SentenceTransformer

from embeddings.embedding_config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIMENSION,
    NORMALIZE_EMBEDDINGS,
)


class EmbeddingModel:
    """
    Wrapper around the Sentence Transformers embedding model.
    """

    def __init__(self):
        print(
            f"Loading embedding model: "
            f"{EMBEDDING_MODEL_NAME}"
        )

        self.model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

        self.dimension = EMBEDDING_DIMENSION

        print("Embedding model loaded successfully.")

    def embed_text(self, text: str):
        """
        Generate an embedding for a single text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        embedding = self.model.encode(
            text,
            normalize_embeddings=NORMALIZE_EMBEDDINGS,
        )

        return embedding.tolist()

    def embed_documents(self, texts):
        """
        Generate embeddings for multiple documents.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=NORMALIZE_EMBEDDINGS,
        )

        return embeddings.tolist()

    def get_dimension(self):
        """
        Return embedding vector dimension.
        """

        return self.dimension