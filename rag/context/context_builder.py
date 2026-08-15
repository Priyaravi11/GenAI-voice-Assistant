class ContextBuilder:
    """
    Builds a clean context structure for the LLM
    using customer information and retrieved documents.
    """

    def __init__(self, max_context_documents=3):
        self.max_context_documents = max_context_documents

    def build(
        self,
        request_id,
        customer_context,
        customer_query,
        retrieved_context,
        response_requirements
    ):
        """
        Build the final LLM-ready context.
        """

        # -------------------------------------------------
        # STEP 1: Limit retrieved documents
        # -------------------------------------------------

        retrieved_context = retrieved_context[
            :self.max_context_documents
        ]

        # -------------------------------------------------
        # STEP 2: Clean retrieved documents
        # -------------------------------------------------

        formatted_context = []

        for document in retrieved_context:

            formatted_context.append(
                {
                    "content": document.get(
                        "content",
                        ""
                    ),

                    "relevance_score": document.get(
                        "relevance_score",
                        0
                    ),

                    "source": document.get(
                        "metadata",
                        {}
                    ).get(
                        "source"
                    ),

                    "language": document.get(
                        "metadata",
                        {}
                    ).get(
                        "language",
                        "en"
                    )
                }
            )

        # -------------------------------------------------
        # STEP 3: Build final structure
        # -------------------------------------------------

        llm_context = {
            "request_id": request_id,

            "customer_context": customer_context,

            "customer_query": customer_query,

            "retrieved_context": formatted_context,

            "response_requirements": response_requirements
        }

        return llm_context