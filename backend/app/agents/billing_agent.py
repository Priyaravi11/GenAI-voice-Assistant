import logging
from typing import Any, Dict, Optional

from app.gemini import generate_text
from app.rag import rag_service

from tools.billing_tool import (
    get_current_bill,
    get_previous_bill,
    get_bill_history,
    check_duplicate_bill,
)


logger = logging.getLogger(__name__)


class BillingAgent:
    """
    Billing Agent

    Handles:
        - Current bill
        - Previous bill
        - Billing history
        - Duplicate bills
        - Billing policy / general billing questions

    Communication:

        User
          ↓
        Billing Agent
          ↓
        RAG + Billing Tool
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
                "Invalid billing query."
            )

        query = query.strip()

        if not query:
            return self._error_response(
                "Billing query cannot be empty."
            )

        try:

            # --------------------------------------------------
            # 1. Retrieve billing knowledge from RAG
            # --------------------------------------------------

            rag_context = self._retrieve_rag(
                query=query,
                context=context,
            )

            # --------------------------------------------------
            # 2. Decide whether a billing tool is required
            # --------------------------------------------------

            billing_data = None

            tool_name = self._select_billing_tool(query)

            if tool_name:

                customer_id = context.get(
                    "customer_id"
                )

                if not customer_id:

                    logger.warning(
                        "Customer ID not found in context."
                    )

                    return {
                        "agent": "billing",
                        "response": (
                            "Sure, I can check your billing "
                            "information. Could you please "
                            "provide your customer ID?"
                        ),
                        "success": True,
                        "tool_used": None,
                        "requires_customer_id": True,
                    }

                else:

                    billing_data = self._call_billing_tool(
                        tool_name=tool_name,
                        customer_id=customer_id,
                    )

            # --------------------------------------------------
            # 3. Generate final answer using Gemini
            # --------------------------------------------------

            response = await self._generate_response(
                query=query,
                rag_context=rag_context,
                billing_data=billing_data,
                context=context,
            )

            return {
                "agent": "billing",
                "response": response,
                "success": True,
                "tool_used": tool_name,
            }

        except Exception as exc:

            logger.exception(
                "Billing Agent failed: %s",
                exc,
            )

            return self._error_response(
                "I'm sorry, I couldn't process your "
                "billing request right now."
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
                "billing-agent",
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
    # TOOL SELECTION
    # ==========================================================

    @staticmethod
    def _select_billing_tool(
        query: str,
    ) -> Optional[str]:
        """
        Decide which billing tool should be called.

        Available tools:

            get_current_bill()
            get_previous_bill()
            get_bill_history()
            check_duplicate_bill()
        """

        text = query.lower()

        # ------------------------------------------------------
        # Duplicate bill
        # ------------------------------------------------------

        duplicate_keywords = [
            "duplicate bill",
            "duplicate billing",
            "charged twice",
            "billed twice",
            "bill twice",
            "same bill twice",
            "double charge",
            "double billing",
        ]

        if any(
            keyword in text
            for keyword in duplicate_keywords
        ):
            return "check_duplicate_bill"

        # ------------------------------------------------------
        # Billing history
        # ------------------------------------------------------

        history_keywords = [
            "billing history",
            "bill history",
            "billing records",
            "previous bills",
            "past bills",
            "old bills",
            "all my bills",
            "show my bills",
        ]

        if any(
            keyword in text
            for keyword in history_keywords
        ):
            return "get_bill_history"

        # ------------------------------------------------------
        # Previous bill
        # ------------------------------------------------------

        previous_keywords = [
            "previous bill",
            "last bill",
            "old bill",
            "last month's bill",
            "previous month's bill",
            "previous invoice",
        ]

        if any(
            keyword in text
            for keyword in previous_keywords
        ):
            return "get_previous_bill"

        # ------------------------------------------------------
        # Current bill
        # ------------------------------------------------------

        current_bill_keywords = [
            "my bill",
            "current bill",
            "current invoice",
            "my invoice",
            "bill amount",
            "how much is my bill",
            "how much do i owe",
            "what do i owe",
            "why is my bill",
            "why was i charged",
            "my charges",
            "my charge",
        ]

        if any(
            keyword in text
            for keyword in current_bill_keywords
        ):
            return "get_current_bill"

        # ------------------------------------------------------
        # No customer-specific tool required
        # ------------------------------------------------------

        return None

    # ==========================================================
    # BILLING TOOL EXECUTION
    # ==========================================================

    @staticmethod
    def _call_billing_tool(
        tool_name: str,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Call the exact billing tool function.

        These functions are synchronous in the current
        billing_tool.py, so we DO NOT use await.
        """

        if tool_name == "get_current_bill":

            return get_current_bill(
                customer_id
            )

        if tool_name == "get_previous_bill":

            return get_previous_bill(
                customer_id
            )

        if tool_name == "get_bill_history":

            return get_bill_history(
                customer_id
            )

        if tool_name == "check_duplicate_bill":

            return check_duplicate_bill(
                customer_id
            )

        logger.warning(
            "Unknown billing tool: %s",
            tool_name,
        )

        return {
            "success": False,
            "message": "Unknown billing tool."
        }

    # ==========================================================
    # GEMINI RESPONSE
    # ==========================================================

    async def _generate_response(
        self,
        query: str,
        rag_context: Any,
        billing_data: Any,
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
You are the Billing Agent of a multilingual
telecom customer-care voice assistant.

Your job is to answer the customer's billing question.

Supported languages:
English, Tamil, Hindi, Telugu, Kannada and Malayalam.

IMPORTANT RULES:

1. Respond in the same language as the customer.
2. Use the retrieved billing knowledge when relevant.
3. Use the customer billing data when it is available.
4. Never invent billing information.
5. Never invent bill amounts, charges, dates or invoices.
6. If the billing tool reports that customer data was not found,
   clearly explain that the billing information is unavailable.
7. If the tool reports a duplicate bill, clearly explain the
   duplicate billing information.
8. If billing history is provided, summarize it clearly.
9. Keep the answer concise because this is a voice assistant.
10. Do not mention RAG, tools, Gemini, prompts or internal agents.
11. Do not expose unnecessary sensitive customer information.
12. If the available information is insufficient, ask a useful
    clarification question.

Preferred language:
{language}

Conversation history:
{history}

Retrieved billing knowledge:
{rag_context}

Customer billing data:
{billing_data}

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
                "Gemini billing response generation failed: %s",
                exc,
            )

        return (
            "I'm sorry, I couldn't generate a billing "
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
            "agent": "billing",
            "response": message,
            "success": False,
        }


# =============================================================
# SHARED BILLING AGENT INSTANCE
# =============================================================

billing_agent = BillingAgent()