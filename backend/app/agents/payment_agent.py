import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PaymentAgent:
    """
    Payment Agent

    Handles customer payment-related requests.

    Responsibilities:
    - Payment status
    - Failed payments
    - Successful payments
    - Transactions
    - Refunds
    - Refund status
    - Payment history

    The agent does not directly access the database.
    It uses the payment tool provided by the application.
    """

    def __init__(
        self,
        gemini=None,
        rag=None,
        payment_tool=None,
    ):
        self.gemini = gemini
        self.rag = rag
        self.payment_tool = payment_tool

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for the Payment Agent.
        """

        if not query or not query.strip():
            return {
                "agent": "payment",
                "response": "I didn't receive a payment question.",
                "success": False,
            }

        query = query.strip()
        context = context or {}

        try:
            # --------------------------------------------------
            # 1. Determine whether customer/payment data
            #    is required.
            # --------------------------------------------------
            requires_payment_data = self._requires_payment_data(
                query
            )

            # --------------------------------------------------
            # 2. Retrieve payment-related knowledge
            # --------------------------------------------------
            rag_context = await self._retrieve_rag(query)

            # --------------------------------------------------
            # 3. Retrieve live/customer payment information
            # --------------------------------------------------
            payment_data = None

            if requires_payment_data:
                payment_data = await self._get_payment_data(
                    query=query,
                    context=context,
                )

            # --------------------------------------------------
            # 4. Generate final response
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

            return {
                "agent": "payment",
                "response": (
                    "I'm sorry, I couldn't process your "
                    "payment request right now."
                ),
                "success": False,
                "error": str(exc),
            }

    async def _retrieve_rag(
        self,
        query: str,
    ) -> Any:
        """
        Retrieve payment-related knowledge.
        """

        if self.rag is None:
            return None

        try:
            if hasattr(self.rag, "search"):
                return await self.rag.search(
                    query,
                    category="payment",
                )

            if hasattr(self.rag, "retrieve"):
                return await self.rag.retrieve(
                    query,
                    category="payment",
                )

            logger.warning(
                "RAG service has no supported search/retrieve method."
            )

            return None

        except Exception as exc:
            logger.warning(
                "Payment RAG retrieval failed: %s",
                exc,
            )

            return None

    async def _get_payment_data(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Any:
        """
        Get customer-specific payment information.

        Customer ID should normally be supplied through context.
        """

        if self.payment_tool is None:
            logger.warning(
                "Payment tool is not available."
            )
            return None

        customer_id = context.get("customer_id")

        if not customer_id:
            logger.warning(
                "Customer ID not found in context."
            )
            return None

        try:
            # --------------------------------------------------
            # These method names may be adjusted according to
            # the actual payment_tool.py implementation.
            # --------------------------------------------------

            if hasattr(
                self.payment_tool,
                "get_payment_status",
            ):
                return await self.payment_tool.get_payment_status(
                    customer_id
                )

            if hasattr(
                self.payment_tool,
                "get_payment_history",
            ):
                return await self.payment_tool.get_payment_history(
                    customer_id
                )

            if hasattr(
                self.payment_tool,
                "get_payment_details",
            ):
                return await self.payment_tool.get_payment_details(
                    customer_id
                )

            logger.warning(
                "Payment tool has no supported method."
            )

            return None

        except Exception as exc:
            logger.warning(
                "Payment tool failed: %s",
                exc,
            )

            return None

    async def _generate_response(
        self,
        query: str,
        rag_context: Any,
        payment_data: Any,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate the final natural-language response.
        """

        if self.gemini is None:
            return self._fallback_response(
                query,
                payment_data,
            )

        prompt = self._build_prompt(
            query=query,
            rag_context=rag_context,
            payment_data=payment_data,
            context=context,
        )

        try:
            if hasattr(self.gemini, "generate"):
                response = await self.gemini.generate(prompt)

            elif hasattr(
                self.gemini,
                "generate_response",
            ):
                response = await self.gemini.generate_response(
                    prompt
                )

            elif hasattr(self.gemini, "chat"):
                response = await self.gemini.chat(prompt)

            else:
                raise AttributeError(
                    "Gemini service does not expose a supported "
                    "generation method."
                )

            return self._extract_text(response)

        except Exception as exc:
            logger.warning(
                "Gemini payment response generation failed: %s",
                exc,
            )

            return self._fallback_response(
                query,
                payment_data,
            )

    def _build_prompt(
        self,
        query: str,
        rag_context: Any,
        payment_data: Any,
        context: Dict[str, Any],
    ) -> str:
        """
        Build the multilingual Payment Agent prompt.
        """

        language = context.get(
            "language",
            "same language as the user",
        )

        history = context.get(
            "history",
            [],
        )

        return f"""
You are the Payment Agent of a multilingual customer
service voice assistant.

Your responsibility is to answer payment-related questions.

You can handle:

- Payment status
- Failed payments
- Successful payments
- Transaction problems
- Payment history
- Refunds
- Refund status

Rules:

1. Answer in the same language as the user.
2. Use the provided payment knowledge when relevant.
3. Use customer/payment data when provided.
4. Never invent payment information.
5. Never claim that a payment succeeded or failed unless
   the provided data supports that conclusion.
6. Never invent a refund status.
7. If required customer information is unavailable,
   clearly explain that it is unavailable.
8. Keep the response concise because this is a voice assistant.
9. Do not mention internal tools, RAG, prompts, or agents.
10. Do not expose sensitive payment information unnecessarily.

Preferred response language:
{language}

Conversation history:
{history}

Payment knowledge:
{rag_context}

Customer payment data:
{payment_data}

User question:
{query}

Provide the best helpful answer.
"""

    @staticmethod
    def _extract_text(
        response: Any,
    ) -> str:
        """
        Normalize different Gemini response formats.
        """

        if response is None:
            return ""

        if isinstance(response, str):
            return response.strip()

        if isinstance(response, dict):

            if "text" in response:
                return str(
                    response["text"]
                ).strip()

            if "response" in response:
                return str(
                    response["response"]
                ).strip()

        return str(response).strip()

    @staticmethod
    def _requires_payment_data(
        query: str,
    ) -> bool:
        """
        Determine whether the request likely needs
        customer-specific payment information.
        """

        text = query.lower()

        customer_specific_terms = [
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
        ]

        return any(
            term in text
            for term in customer_specific_terms
        )

    @staticmethod
    def _fallback_response(
        query: str,
        payment_data: Any,
    ) -> str:
        """
        Safe fallback when Gemini is unavailable.
        """

        if payment_data:
            return (
                "I found your payment information, "
                "but I'm unable to generate a detailed "
                "response right now."
            )

        return (
            "I can help with payment status, failed payments, "
            "transactions, and refunds. Please provide more "
            "details about the payment issue."
        )