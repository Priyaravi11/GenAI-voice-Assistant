import logging
from typing import Any, Dict, Optional

from app.gemini import generate_text
from app.rag import rag_service

from tools.payment_tool import (
    get_payment_status,
    get_payment_history,
    get_latest_payment,
    get_payment_issue,
)


logger = logging.getLogger(__name__)


class PaymentAgent:
    """
    Payment Agent

    Handles:
        - Payment status
        - Payment history
        - Latest payment
        - Failed payments
        - Pending payments
        - Payment issues

    Communication:

        User
          ↓
        Payment Agent
          ↓
        RAG + Payment Tool
          ↓
        Gemini
          ↓
        Final Response
    """

    # ==========================================================
    # MAIN ENTRY POINT
    # ==========================================================

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

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
            # 1. Retrieve payment knowledge from RAG
            # --------------------------------------------------

            rag_context = self._retrieve_rag(
                query=query,
                context=context,
            )

            # --------------------------------------------------
            # 2. Decide which payment tool is required
            # --------------------------------------------------

            payment_data = None

            tool_name = self._select_payment_tool(
                query
            )

            if tool_name:

                customer_id = context.get(
                    "customer_id"
                )

                if not customer_id:

                    logger.warning(
                        "Customer ID not found in context."
                    )

                    return {
                        "agent": "payment",
                        "response": (
                            "Sure, I can check your payment "
                            "information. Could you please "
                            "provide your customer ID?"
                        ),
                        "success": True,
                        "tool_used": None,
                        "requires_customer_id": True,
                    }

                else:

                    payment_data = self._call_payment_tool(
                        tool_name=tool_name,
                        customer_id=customer_id,
                    )

            # --------------------------------------------------
            # 3. Generate final response using Gemini
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
                "tool_used": tool_name,
            }

        except Exception as exc:

            logger.exception(
                "Payment Agent failed: %s",
                exc,
            )

            return self._error_response(
                "I'm sorry, I couldn't process your "
                "payment request right now."
            )

    # ==========================================================
    # RAG
    # ==========================================================

    def _retrieve_rag(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

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

            # Your RAG search() is synchronous.
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
    # PAYMENT TOOL SELECTION
    # ==========================================================

    @staticmethod
    def _select_payment_tool(
        query: str,
    ) -> Optional[str]:
        """
        Decide which payment tool should be called.

        Available tools:

            get_payment_status()
            get_payment_history()
            get_latest_payment()
            get_payment_issue()
        """

        text = query.lower()

        # ------------------------------------------------------
        # Payment issue
        # ------------------------------------------------------

        issue_keywords = [
            "payment failed",
            "payment fail",
            "payment didn't go through",
            "payment did not go through",
            "payment problem",
            "payment issue",
            "payment pending",
            "pending payment",
            "failed payment",
            "why did my payment fail",
            "why was my payment declined",
        ]

        if any(
            keyword in text
            for keyword in issue_keywords
        ):
            return "get_payment_issue"

        # ------------------------------------------------------
        # Payment history
        # ------------------------------------------------------

        history_keywords = [
            "payment history",
            "payment records",
            "past payments",
            "previous payments",
            "old payments",
            "show my payments",
            "all my payments",
        ]

        if any(
            keyword in text
            for keyword in history_keywords
        ):
            return "get_payment_history"

        # ------------------------------------------------------
        # Latest payment
        # ------------------------------------------------------

        latest_keywords = [
            "latest payment",
            "last payment",
            "recent payment",
            "most recent payment",
            "my last payment",
        ]

        if any(
            keyword in text
            for keyword in latest_keywords
        ):
            return "get_latest_payment"

        # ------------------------------------------------------
        # Payment status
        # ------------------------------------------------------

        status_keywords = [
            "payment status",
            "status of my payment",
            "did my payment go through",
            "was my payment successful",
            "is my payment successful",
            "did i pay",
            "has my payment gone through",
            "payment successful",
        ]

        if any(
            keyword in text
            for keyword in status_keywords
        ):
            return "get_payment_status"

        # ------------------------------------------------------
        # Generic customer payment question
        # ------------------------------------------------------

        generic_payment_keywords = [
            "my payment",
            "my transaction",
            "payment",
        ]

        if any(
            keyword in text
            for keyword in generic_payment_keywords
        ):
            return "get_payment_status"

        return None

    # ==========================================================
    # PAYMENT TOOL EXECUTION
    # ==========================================================

    @staticmethod
    def _call_payment_tool(
        tool_name: str,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Call the exact payment tool function.

        The functions in payment_tool.py are synchronous,
        so we DO NOT use await.
        """

        if tool_name == "get_payment_status":

            return get_payment_status(
                customer_id
            )

        if tool_name == "get_payment_history":

            return get_payment_history(
                customer_id
            )

        if tool_name == "get_latest_payment":

            return get_latest_payment(
                customer_id
            )

        if tool_name == "get_payment_issue":

            return get_payment_issue(
                customer_id
            )

        logger.warning(
            "Unknown payment tool: %s",
            tool_name,
        )

        return {
            "success": False,
            "message": "Unknown payment tool."
        }

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

Supported languages:
English, Tamil, Hindi, Telugu, Kannada and Malayalam.

You can handle:
- Payment status
- Payment history
- Latest payment
- Failed payments
- Pending payments
- Payment issues

IMPORTANT RULES:

1. Respond in the same language as the customer.
2. Use the retrieved payment knowledge when relevant.
3. Use customer payment data when it is available.
4. Never invent payment information.
5. Never invent transaction IDs, payment amounts or dates.
6. Never say a payment was successful unless the provided
   payment data supports it.
7. Never say a payment failed unless the provided payment
   data supports it.
8. If the payment tool reports no record, clearly explain
   that no payment record was found.
9. If a payment is pending, clearly explain that it is pending.
10. If a payment has failed, explain the failure reason when
    the provided data contains one.
11. Keep the answer concise because this is a voice assistant.
12. Do not mention RAG, tools, Gemini, prompts or internal agents.
13. Do not expose unnecessary sensitive payment information.
14. If the available information is insufficient, ask a useful
    clarification question.

Preferred language:
{language}

Conversation history:
{history}

Retrieved payment knowledge:
{rag_context}

Customer payment data:
{payment_data}

Customer question:
{query}

Give only the final customer-facing answer.
"""

        try:

            response = await generate_text(
                prompt
            )

            if response and response.strip():
                return response.strip()

        except Exception as exc:

            logger.exception(
                "Gemini payment response generation failed: %s",
                exc,
            )

        return (
            "I'm sorry, I couldn't generate a payment "
            "response right now."
        )

    # ==========================================================
    # ERROR RESPONSE
    # ==========================================================

    @staticmethod
    def _error_response(
        message: str,
    ) -> Dict[str, Any]:

        return {
            "agent": "payment",
            "response": message,
            "success": False,
        }


# =============================================================
# SHARED PAYMENT AGENT INSTANCE
# =============================================================

payment_agent = PaymentAgent()