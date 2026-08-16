import chromadb
from sentence_transformers import SentenceTransformer

from .query_builder import QueryBuilder
from .context_builder import ContextBuilder


class Retriever:

    def __init__(
        self,
        chroma_path="rag/chroma",
        collection_name="customer_care_knowledge",
        embedding_model="BAAI/bge-small-en-v1.5"
    ):

        self.embedding_model = SentenceTransformer(
            embedding_model
        )

        self.client = chromadb.PersistentClient(
            path=chroma_path
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        self.query_builder = QueryBuilder()
        self.context_builder = ContextBuilder()


    def retrieve(
        self,
        query: str,
        category: str | None = None,
        customer_id: str | None = None,
        top_k: int = 5
    ):

        # -------------------------
        # 1. Validate input
        # -------------------------

        if not query or not query.strip():
            return {
                "success": False,
                "documents": [],
                "reason": "Query cannot be empty"
            }

        if top_k <= 0:
            return {
                "success": False,
                "documents": [],
                "reason": "top_k must be greater than 0"
            }


        # -------------------------
        # 2. Build query
        # -------------------------

        request = self.query_builder.build(
            query=query,
            category=category,
            customer_id=customer_id
        )


        # -------------------------
        # 3. Create BGE embedding
        # -------------------------

        query_embedding = self.embedding_model.encode(
            request["query"],
            normalize_embeddings=True
        ).tolist()


        # -------------------------
        # 4. Build metadata filter
        # -------------------------

        conditions = []

        if request["category"]:
            conditions.append({
                "category": request["category"]
            })

        if request["customer_id"]:
            conditions.append({
                "customer_id": request["customer_id"]
            })


        if len(conditions) == 1:

            where = conditions[0]

        elif len(conditions) > 1:

            where = {
                "$and": conditions
            }

        else:

            where = None


        # -------------------------
        # 5. Search ChromaDB
        # -------------------------

        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances"
            ]
        }

        if where:
            search_kwargs["where"] = where


        try:

            results = self.collection.query(
                **search_kwargs
            )

        except Exception as e:

            return {
                "success": False,
                "documents": [],
                "reason": f"Retrieval failed: {str(e)}"
            }


        # -------------------------
        # 6. Format response
        # -------------------------

        return self.context_builder.build(
            results
        )