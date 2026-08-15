"""
RAG Service
===========

Integration layer between the backend orchestrator/agents
and the existing RAG pipeline.

Responsibilities:
    - Validate NLU input
    - Pass NLU data to QueryProcessor
    - Return LLM-ready RAG context
    - Provide a simple shared RAG service instance

The actual RAG pipeline is implemented in:
    rag/query/query_processor.py
    rag/query/intent_mapper.py
    rag/vector_store/retriever.py
    rag/vector_store/collection.py
    rag/embeddings/embedding_model.py
    rag/context/context_builder.py

This module does NOT:
    - Generate embeddings
    - Query ChromaDB directly
    - Build metadata filters
    - Build prompts
    - Call Gemini
    - Generate the final answer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from rag.query.query_processor import QueryProcessor


logger = logging.getLogger(__name__)


class RAGService:
    """
    Backend service for retrieving knowledge from the RAG pipeline.

    Architecture:

        Orchestrator
              |
              v
          RAGService
              |
              v
        QueryProcessor
              |
              +----> Intent Mapper
              |
              +----> Retriever
              |          |
              |          v
              |       ChromaDB
              |
              +----> ContextBuilder
              |
              v
        LLM-ready context
    """

    def __init__(
        self,
        top_k: int = 3,
        score_threshold: float = 0.50,
    ) -> None:
        """
        Initialize the RAG service.

        Args:
            top_k:
                Maximum number of documents to retrieve.

            score_threshold:
                Minimum relevance score required for
                a retrieved document.

        Raises:
            ValueError:
                If configuration values are invalid.
        """

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(
                "top_k must be a positive integer."
            )

        if not isinstance(score_threshold, (int, float)):
            raise ValueError(
                "score_threshold must be a number."
            )

        if not 0.0 <= float(score_threshold) <= 1.0:
            raise ValueError(
                "score_threshold must be between 0.0 and 1.0."
            )

        self.top_k = top_k
        self.score_threshold = float(score_threshold)

        self.processor = QueryProcessor(
            top_k=self.top_k,
            score_threshold=self.score_threshold,
        )

        logger.info(
            "RAGService initialized: top_k=%s, score_threshold=%s",
            self.top_k,
            self.score_threshold,
        )

    # ==========================================================
    # MAIN RAG METHOD
    # ==========================================================

    def retrieve(
        self,
        nlu_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process NLU output through the RAG pipeline.

        Expected input:

        {
            "request_id": "REQ001",

            "language": {
                "primary": "ta",
                "code_switched": False
            },

            "intent": {
                "name": "billing"
            },

            "entities": {
                "customer_id": "C001"
            },

            "sentiment": {
                "label": "negative"
            },

            "customer_query":
                "My bill is higher this month."
        }

        Returns:

        {
            "request_id": "...",
            "customer_context": {...},
            "customer_query": "...",
            "retrieved_context": [...],
            "response_requirements": {...}
        }

        The returned structure is produced by the existing
        QueryProcessor / ContextBuilder.
        """

        self._validate_nlu_data(nlu_data)

        request_id = nlu_data.get("request_id")

        logger.info(
            "Starting RAG retrieval: request_id=%s",
            request_id,
        )

        try:
            result = self.processor.process(
                nlu_data
            )

        except Exception:
            logger.exception(
                "RAG retrieval failed: request_id=%s",
                request_id,
            )
            raise

        retrieved_count = len(
            result.get(
                "retrieved_context",
                []
            )
        )

        logger.info(
            "RAG retrieval completed: request_id=%s, "
            "documents=%s",
            request_id,
            retrieved_count,
        )

        return result

    # ==========================================================
    # OPTIONAL SIMPLE QUERY METHOD
    # ==========================================================

    def search(
        self,
        query: str,
        request_id: str = "rag-direct",
        language: str = "en",
        intent: str = "general",
        entities: Optional[Dict[str, Any]] = None,
        sentiment: str = "neutral",
        code_switched: bool = False,
    ) -> Dict[str, Any]:
        """
        Convenience method for directly querying RAG.

        This method is useful for:
            - testing
            - debugging
            - unit tests
            - simple backend calls

        The main production path should normally use
        `retrieve()` with complete NLU output.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty."
            )

        if not request_id:
            raise ValueError(
                "request_id cannot be empty."
            )

        if not language:
            language = "en"

        if not intent:
            intent = "general"

        if entities is None:
            entities = {}

        nlu_data = {
            "request_id": request_id,

            "language": {
                "primary": language,
                "code_switched": code_switched,
            },

            "intent": {
                "name": intent,
            },

            "entities": entities,

            "sentiment": {
                "label": sentiment,
            },

            "customer_query": query,
        }

        return self.retrieve(
            nlu_data
        )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @staticmethod
    def _validate_nlu_data(
        nlu_data: Dict[str, Any],
    ) -> None:
        """
        Validate the minimum NLU structure required by
        QueryProcessor.

        QueryProcessor performs its own validation as well.
        This validation provides an earlier and clearer
        error at the service boundary.
        """

        if not isinstance(nlu_data, dict):
            raise TypeError(
                "nlu_data must be a dictionary."
            )

        if not nlu_data:
            raise ValueError(
                "nlu_data cannot be empty."
            )

        # ------------------------------------------------------
        # request_id
        # ------------------------------------------------------

        request_id = nlu_data.get(
            "request_id"
        )

        if not request_id:
            raise ValueError(
                "nlu_data.request_id is required."
            )

        # ------------------------------------------------------
        # language
        # ------------------------------------------------------

        language = nlu_data.get(
            "language"
        )

        if language is not None and not isinstance(
            language,
            dict,
        ):
            raise TypeError(
                "nlu_data.language must be a dictionary."
            )

        # ------------------------------------------------------
        # intent
        # ------------------------------------------------------

        intent = nlu_data.get(
            "intent"
        )

        if not isinstance(
            intent,
            dict,
        ):
            raise TypeError(
                "nlu_data.intent must be a dictionary."
            )

        if not intent.get("name"):
            raise ValueError(
                "nlu_data.intent.name is required."
            )

        # ------------------------------------------------------
        # entities
        # ------------------------------------------------------

        entities = nlu_data.get(
            "entities",
            {},
        )

        if not isinstance(
            entities,
            dict,
        ):
            raise TypeError(
                "nlu_data.entities must be a dictionary."
            )

        # ------------------------------------------------------
        # sentiment
        # ------------------------------------------------------

        sentiment = nlu_data.get(
            "sentiment"
        )

        if sentiment is not None and not isinstance(
            sentiment,
            dict,
        ):
            raise TypeError(
                "nlu_data.sentiment must be a dictionary."
            )

        # ------------------------------------------------------
        # customer query
        # ------------------------------------------------------

        customer_query = nlu_data.get(
            "customer_query"
        )

        if not isinstance(
            customer_query,
            str,
        ):
            raise TypeError(
                "nlu_data.customer_query must be a string."
            )

        if not customer_query.strip():
            raise ValueError(
                "nlu_data.customer_query cannot be empty."
            )


# ==============================================================
# SHARED SERVICE INSTANCE
# ==============================================================

rag_service = RAGService(
    top_k=3,
    score_threshold=0.50,
)


# ==============================================================
# PUBLIC HELPER
# ==============================================================

def retrieve_context(
    nlu_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Public helper used by the orchestrator or agents.

    Example:

        from app.rag import retrieve_context

        rag_context = retrieve_context(
            nlu_data
        )
    """

    return rag_service.retrieve(
        nlu_data
    )