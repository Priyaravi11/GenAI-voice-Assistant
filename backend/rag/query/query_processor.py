from vector_store.retriever import Retriever
from query.intent_mapper import build_metadata_filter
from context.context_builder import ContextBuilder


class QueryProcessor:
    """
    Converts NLU output into an LLM-ready RAG context.

    Flow:

    NLU JSON
        ↓
    English customer query
        ↓
    Intent + entity metadata filter
        ↓
    ChromaDB retrieval
        ↓
    Context Builder
        ↓
    LLM-ready output
    """

    def __init__(
        self,
        top_k=3,
        score_threshold=0.50
    ):
        # -------------------------------------------------
        # Retriever
        # -------------------------------------------------

        self.retriever = Retriever(
            top_k=top_k,
            score_threshold=score_threshold
        )

        # -------------------------------------------------
        # Context Builder
        # -------------------------------------------------

        self.context_builder = ContextBuilder(
            max_context_documents=top_k
        )

        self.top_k = top_k

    # =====================================================
    # PROCESS NLU OUTPUT
    # =====================================================

    def process(self, nlu_data):
        """
        Process NLU output and generate the final
        LLM-ready RAG context.
        """

        # -------------------------------------------------
        # STEP 1: Validate NLU data
        # -------------------------------------------------

        if not nlu_data:
            raise ValueError(
                "NLU data cannot be empty."
            )

        # -------------------------------------------------
        # STEP 2: Extract request ID
        # -------------------------------------------------

        request_id = nlu_data.get(
            "request_id"
        )

        if not request_id:
            raise ValueError(
                "request_id is required."
            )

        # -------------------------------------------------
        # STEP 3: Extract language
        # -------------------------------------------------

        language_data = nlu_data.get(
            "language",
            {}
        )

        primary_language = language_data.get(
            "primary",
            "en"
        )

        code_switched = language_data.get(
            "code_switched",
            False
        )

        # -------------------------------------------------
        # STEP 4: Extract intent
        # -------------------------------------------------

        intent_data = nlu_data.get(
            "intent",
            {}
        )

        intent = intent_data.get(
            "name"
        )

        if not intent:
            raise ValueError(
                "Intent is required."
            )

        # -------------------------------------------------
        # STEP 5: Extract entities
        # -------------------------------------------------

        entities = nlu_data.get(
            "entities",
            {}
        )

        # -------------------------------------------------
        # STEP 6: Extract sentiment
        # -------------------------------------------------

        sentiment_data = nlu_data.get(
            "sentiment",
            {}
        )

        sentiment = sentiment_data.get(
            "label"
        )

        # -------------------------------------------------
        # STEP 7: Extract English customer query
        # -------------------------------------------------

        customer_query = nlu_data.get(
            "customer_query"
        )

        if not customer_query:
            raise ValueError(
                "customer_query is required."
            )

        # -------------------------------------------------
        # STEP 8: Build customer context
        # -------------------------------------------------

        customer_context = {
            "language": primary_language,

            "code_switched": code_switched,

            "intent": intent,

            "entities": entities,

            "sentiment": sentiment
        }

        # -------------------------------------------------
        # STEP 9: Build metadata filter
        # -------------------------------------------------

        metadata_filter = build_metadata_filter(
            nlu_data
        )

        # -------------------------------------------------
        # STEP 10: Retrieve relevant documents
        # -------------------------------------------------

        retrieved_documents = self.retriever.search(
            customer_query,
            metadata_filter
        )

        # -------------------------------------------------
        # STEP 11: Build response requirements
        # -------------------------------------------------

        response_requirements = {
            "language": primary_language,

            "use_context_only": True,

            "do_not_invent_information": True
        }

        # -------------------------------------------------
        # STEP 12: Build final LLM context
        # -------------------------------------------------

        final_context = self.context_builder.build(
            request_id=request_id,

            customer_context=customer_context,

            customer_query=customer_query,

            retrieved_context=retrieved_documents,

            response_requirements=response_requirements
        )

        # -------------------------------------------------
        # STEP 13: Return final LLM-ready context
        # -------------------------------------------------

        return final_context