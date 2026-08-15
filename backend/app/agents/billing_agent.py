import logging
from typing import Any, Dict, Optional

from app.gemini import generate_text
from app.rag import rag_service


logger = logging.getLogger(__name__)


class BillingAgent:
    """
    Billing Agent

    Handles:
        - Current bill
        - Billing history
        - Charges
        - Invoices
        - Due dates
        - Late fees
        - Billing-related questions

    Communication:

        User
          ↓
        Billing Agent
          ↓
        RAG
          ↓
        Billing Tool (when available)
          ↓
        Gemini
          ↓
        Final response
    """

    def __init__(self, billing_tool=None):
        """
        billing_tool is injected later by the orchestrator.

        We keep it optional because the actual billing_tool.py
        is not available yet.
        """
        self.billing_tool = billing_tool

    # ==========================================================
    # MAIN ENTRY POINT
    # ==========================================================

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main method used by the orchestrator.

        Example:

            result = await billing_agent.handle(
                "Why is my bill so high?",
                context
            )
        """

        context = context or {}

        if not isinstance(query, str):
            return self._error_response(
                "Invalid billing query."
            )

        query = query.strip()

        if not query:
            return self._error_response(
                "Billing query cannot be empty."
            )

        try:

            # --------------------------------------------------
            # 1. Retrieve billing knowledge
            # --------------------------------------------------

            rag_context = self._retrieve_billing_knowledge(
                query=query,
                context=context,
            )

            # --------------------------------------------------
            # 2. Get customer-specific billing information
            #    when required
            # --------------------------------------------------

            customer_data = None

            if self._requires_customer_data(query):

                customer_data = await self._get_customer_billing(
                    query=query,
                    context=context,
                )

            # --------------------------------------------------
            # 3. Generate final answer using Gemini
            # --------------------------------------------------

            response = await self._generate_response(
                query=query,
                rag_context=rag_context,
                customer_data=customer_data,
                context=context,
            )

            return {
                "agent": "billing",
                "response": response,
                "success": True,
            }

        except Exception as exc:

            logger.exception(
                "Billing Agent failed: %s",
                exc,
            )

            return self._error_response(
                "I’m sorry, I couldn't process your billing "
                "request right now."
            )

    # ==========================================================
    # RAG
    # ==========================================================

    def _retrieve_billing_knowledge(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve billing knowledge using the existing RAGService.

        Your actual RAG interface is:

            rag_service.search(
                query=...,
                request_id=...,
                language=...,
                intent=...,
                entities=...,
                sentiment=...,
                code_switched=...
            )

        RAG is synchronous, so we DO NOT use await here.
        """

        try:

            request_id = context.get(
                "request_id",
                "billing-agent",
            )

            language = context.get(
                "language",
                "en",
            )

            # --------------------------------------------------
            # Your context may contain language as:
            #
            # "ta"
            #
            # or:
            #
            # {"primary": "ta"}
            # --------------------------------------------------

            if isinstance(language, dict):

                language = language.get(
                    "primary",
                    "en",
                )

            entities = context.get(
                "entities",
                {},
            )

            sentiment = context.get(
                "sentiment",
                "neutral",
            )

            if isinstance(sentiment, dict):

                sentiment = sentiment.get(
                    "label",
                    "neutral",
                )

            code_switched = context.get(
                "code_switched",
                False,
            )

            rag_result = rag_service.search(
                query=query,
                request_id=request_id,
                language=language,
                intent="billing",
                entities=entities,
                sentiment=sentiment,
                code_switched=code_switched,
            )

            return rag_result

        except Exception as exc:

            logger.exception(
                "Billing RAG retrieval failed: %s",
                exc,
            )

            return None

    # ==========================================================
    # BILLING TOOL
    # ==========================================================

    async def _get_customer_billing(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Any:
        """
        Retrieve customer-specific billing information.

        The exact billing tool method will be connected once
        billing_tool.py is available.
        """

        if self.billing_tool is None:

            logger.info(
                "Billing tool is not available yet."
            )

            return None

        customer_id = context.get(
            "customer_id"
        )

        if not customer_id:

            logger.warning(
                "Customer ID not found in context."
            )

            return None

        try:

            # --------------------------------------------------
            # Temporary adapter.
            #
            # Once the actual billing_tool.py is available,
            # replace this with its exact method.
            # --------------------------------------------------

            if hasattr(
                self.billing_tool,
                "get_bill",
            ):

                result = self.billing_tool.get_bill(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            if hasattr(
                self.billing_tool,
                "get_billing_details",
            ):

                result = self.billing_tool.get_billing_details(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            if hasattr(
                self.billing_tool,
                "get_billing_history",
            ):

                result = self.billing_tool.get_billing_history(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            logger.warning(
                "No supported billing tool method found."
            )

            return None

        except Exception as exc:

            logger.exception(
                "Billing tool failed: %s",
                exc,
            )

            return None

    # ==========================================================
    # GEMINI RESPONSE
    # ==========================================================

    async def _generate_response(
        self,
        query: str,
        rag_context: Any,
        customer_data: Any,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate the final customer-facing response.

        Uses the actual generate_text() function from gemini.py.
        """

        language = context.get(
            "language",
            "en",
        )

        if isinstance(language, dict):

            language = language.get(
                "primary",
                "en",
            )

        history = context.get(
            "history",
            [],
        )

        prompt = f"""
You are the Billing Agent of a multilingual
telecom customer-care voice assistant.

Your job is to answer the customer's billing question.

Supported languages include:
English, Tamil, Hindi, Telugu, Kannada and Malayalam.

IMPORTANT RULES:

1. Respond in the same language as the customer.
2. Use the retrieved billing knowledge when relevant.
3. Use customer billing information only when it is provided.
4. Never invent customer billing information.
5. Never invent a bill amount, charge, invoice or due date.
6. If customer-specific billing information is unavailable,
   clearly say that you need to check the customer's account.
7. Keep the answer concise because this is a voice assistant.
8. Do not mention RAG, tools, prompts, Gemini or internal agents.
9. Do not expose unnecessary sensitive customer information.
10. If the question cannot be answered from the available
    information, ask a useful clarification question.

Preferred language:
{language}

Conversation history:
{history}

Retrieved billing knowledge:
{rag_context}

Customer billing information:
{customer_data}

Customer question:
{query}

Give only the final customer-facing answer.
"""

        response = await generate_text(prompt)

        if not response or not response.strip():

            return (
                "I'm sorry, I couldn't generate a billing "
                "response right now."
            )

        return response.strip()

    # ==========================================================
    # CUSTOMER DATA DECISION
    # ==========================================================

    @staticmethod
    def _requires_customer_data(
        query: str,
    ) -> bool:
        """
        Determine whether the question is about
        the customer's own billing information.
        """

        text = query.lower()

        customer_terms = [
            "my bill",
            "my billing",
            "my invoice",
            "my charge",
            "my charges",
            "my billing history",
            "my bill history",
            "my current bill",
            "my previous bill",
            "my last bill",
            "how much do i owe",
            "what do i owe",
            "why was i charged",
        ]

        return any(
            term in text
            for term in customer_terms
        )

    # ==========================================================
    # ERROR RESPONSE
    # ==========================================================

    @staticmethod
    def _error_response(
        message: str,
    ) -> Dict[str, Any]:
        """
        Standard Billing Agent error response.
        """

        return {
            "agent": "billing",
            "response": message,
            "success": False,
        }


# =============================================================
# SHARED AGENT INSTANCE
# =============================================================

billing_agent = BillingAgent()