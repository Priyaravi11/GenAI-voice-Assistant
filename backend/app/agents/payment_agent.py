import logging
from typing import Any, Dict, Optional

from app.gemini import generate_text
from app.rag import rag_service


logger = logging.getLogger(__name__)


class PaymentAgent:
    """
    Payment Agent

    Handles:
        - Payment status
        - Failed payments
        - Successful payments
        - Transactions
        - Refunds
        - Refund status
        - Payment history

    Communication:

        User
          ↓
        Payment Agent
          ↓
        RAG
          ↓
        Payment Tool (when available)
          ↓
        Gemini
          ↓
        Final response
    """

    def __init__(self, payment_tool=None):
        """
        payment_tool is injected later by the orchestrator.

        The actual payment_tool.py is not available yet,
        so the tool connection remains optional.
        """
        self.payment_tool = payment_tool

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

            result = await payment_agent.handle(
                "Did my payment go through?",
                context
            )
        """

        context = context or {}

        if not isinstance(query, str):
            return self._error_response(
                "Invalid payment query."
            )

        query = query.strip()

        if not query:
            return self._error_response(
                "Payment query cannot be empty."
            )

        try:

            # --------------------------------------------------
            # 1. Retrieve payment knowledge
            # --------------------------------------------------

            rag_context = self._retrieve_payment_knowledge(
                query=query,
                context=context,
            )

            # --------------------------------------------------
            # 2. Get customer-specific payment information
            # --------------------------------------------------

            payment_data = None

            if self._requires_customer_data(query):

                payment_data = await self._get_customer_payment(
                    query=query,
                    context=context,
                )

            # --------------------------------------------------
            # 3. Generate final answer
            # --------------------------------------------------

            response = await self._generate_response(
                query=query,
                rag_context=rag_context,
                payment_data=payment_data,
                context=context,
            )

            return {
                "agent": "payment",
                "response": response,
                "success": True,
            }

        except Exception as exc:

            logger.exception(
                "Payment Agent failed: %s",
                exc,
            )

            return self._error_response(
                "I'm sorry, I couldn't process your payment "
                "request right now."
            )

    # ==========================================================
    # RAG
    # ==========================================================

    def _retrieve_payment_knowledge(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve payment knowledge using the existing RAGService.

        Your actual RAG interface is synchronous, therefore
        we do NOT use await here.
        """

        try:

            request_id = context.get(
                "request_id",
                "payment-agent",
            )

            language = context.get(
                "language",
                "en",
            )

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
                intent="payment",
                entities=entities,
                sentiment=sentiment,
                code_switched=code_switched,
            )

            return rag_result

        except Exception as exc:

            logger.exception(
                "Payment RAG retrieval failed: %s",
                exc,
            )

            return None

    # ==========================================================
    # PAYMENT TOOL
    # ==========================================================

    async def _get_customer_payment(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Any:
        """
        Retrieve customer-specific payment information.

        The exact payment tool method will be connected when
        payment_tool.py is available.
        """

        if self.payment_tool is None:

            logger.info(
                "Payment tool is not available yet."
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
            # Replace with the exact method from
            # payment_tool.py when available.
            # --------------------------------------------------

            if hasattr(
                self.payment_tool,
                "get_payment_status",
            ):

                result = self.payment_tool.get_payment_status(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            if hasattr(
                self.payment_tool,
                "get_payment_details",
            ):

                result = self.payment_tool.get_payment_details(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            if hasattr(
                self.payment_tool,
                "get_payment_history",
            ):

                result = self.payment_tool.get_payment_history(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            if hasattr(
                self.payment_tool,
                "get_refund_status",
            ):

                result = self.payment_tool.get_refund_status(
                    customer_id
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result

            logger.warning(
                "No supported payment tool method found."
            )

            return None

        except Exception as exc:

            logger.exception(
                "Payment tool failed: %s",
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
        payment_data: Any,
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
You are the Payment Agent of a multilingual
telecom customer-care voice assistant.

Your job is to answer the customer's payment-related question.

Supported languages include:
English, Tamil, Hindi, Telugu, Kannada and Malayalam.

You can handle:
- Payment status
- Failed payments
- Successful payments
- Transactions
- Payment history
- Refunds
- Refund status

IMPORTANT RULES:

1. Respond in the same language as the customer.
2. Use the retrieved payment knowledge when relevant.
3. Use customer payment information only when it is provided.
4. Never invent payment information.
5. Never claim that a payment succeeded unless the provided
   payment data says it succeeded.
6. Never claim that a payment failed unless the provided
   payment data supports that conclusion.
7. Never invent a refund status.
8. If customer-specific payment information is unavailable,
   clearly say that you need to check the customer's account.
9. Keep the response concise because this is a voice assistant.
10. Do not mention RAG, tools, prompts, Gemini or internal agents.
11. Do not expose unnecessary sensitive payment information.
12. If the available information is insufficient, ask a
    useful clarification question.

Preferred language:
{language}

Conversation history:
{history}

Retrieved payment knowledge:
{rag_context}

Customer payment information:
{payment_data}

Customer question:
{query}

Give only the final customer-facing answer.
"""

        response = await generate_text(prompt)

        if not response or not response.strip():

            return (
                "I'm sorry, I couldn't generate a payment "
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
        Determine whether the request requires
        customer-specific payment information.
        """

        text = query.lower()

        customer_terms = [
            "my payment",
            "my transaction",
            "my refund",
            "my payment status",
            "payment status",
            "payment history",
            "refund status",
            "did my payment go through",
            "was my payment successful",
            "why did my payment fail",
            "payment failed",
            "payment didn't go through",
            "payment did not go through",
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
        Standard Payment Agent error response.
        """

        return {
            "agent": "payment",
            "response": message,
            "success": False,
        }


# =============================================================
# SHARED AGENT INSTANCE
# =============================================================

payment_agent = PaymentAgent()