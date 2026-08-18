import logging
from typing import Any, Dict, Optional

from backend.app.gemini import generate_text
from backend.app.agents.rag_formatter import build_response_from_rag

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

    def __init__(
        self,
        gemini: Any = None,
        rag: Any = None,
        billing_tool: Any = None,
    ):
        self.gemini = gemini
        self.rag = rag
        self.billing_tool = billing_tool

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
                "I didn't receive a billing question."
            )

        try:

            # --------------------------------------------------
            # 1. Retrieve billing knowledge from RAG
            # --------------------------------------------------

            rag_context = self._retrieve_rag(
                query=query,
                context=context,
            )
            if hasattr(rag_context, "__await__"):
                rag_context = await rag_context

            # --------------------------------------------------
            # 2. Decide whether a billing tool is required
            # --------------------------------------------------

            billing_data = None
            tool_name = self._select_billing_tool(query)

            if tool_name:

                customer_id = context.get(
                    "customer_id"
                )

                # ===================================================
                # CRITICAL: Check for Customer ID before tool call
                # ===================================================
                # If tool requires customer ID but it's missing,
                # return requires_customer_id signal instead of
                # executing the tool.
                # ===================================================

                if not customer_id:

                    logger.info(
                        f"Billing tool '{tool_name}' requires "
                        f"customer ID but none found in context."
                    )

                    return {
                        "agent": "billing",
                        "success": True,
                        "requires_customer_id": True,
                        "tool_used": tool_name,
                        "response": (
                            "Please provide your customer ID."
                        ),
                        "confidence": 1.0,
                        "rag_context": rag_context,
                        "tool_result": None,
                    }

                # ===================================================
                # Customer ID is available, execute tool
                # ===================================================

                billing_data = await self._get_billing_data(
                    query=query,
                    context=context,
                    tool_name=tool_name,
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

            # ===================================================
            # Standardized Result Contract
            # ===================================================

            return {
                "agent": "billing",
                "response": response,
                "success": True,
                "confidence": 0.95,
                "tool_used": tool_name,
                "tool_result": billing_data,
                "rag_context": rag_context,
                "requires_customer_id": False,
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

    async def _get_billing_data(
        self,
        query: str,
        context: Dict[str, Any],
        tool_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        selected_tool = tool_name or self._select_billing_tool(query) or "get_current_bill"
        customer_id = context.get("customer_id")

        if not customer_id:
            return {
                "success": False,
                "requires_customer_id": True,
                "message": "Please provide your customer ID.",
            }

        if self.billing_tool is not None:
            try:
                if selected_tool in ("get_current_bill", "get_previous_bill") and hasattr(
                    self.billing_tool,
                    "get_bill",
                ):
                    result = self.billing_tool.get_bill(customer_id)
                elif selected_tool == "get_bill_history" and hasattr(
                    self.billing_tool,
                    "get_bill_history",
                ):
                    result = self.billing_tool.get_bill_history(customer_id)
                elif selected_tool == "check_duplicate_bill" and hasattr(
                    self.billing_tool,
                    "check_duplicate_bill",
                ):
                    result = self.billing_tool.check_duplicate_bill(customer_id)
                else:
                    result = None

                if hasattr(result, "__await__"):
                    result = await result

                if result is not None:
                    return {
                        "success": True,
                        "data": result,
                    }

            except Exception as exc:
                return {
                    "success": False,
                    "message": "Failed to retrieve billing information",
                    "error": str(exc),
                }

        return self._call_billing_tool(
            tool_name=selected_tool,
            customer_id=customer_id,
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
            if self.rag is not None:
                if hasattr(self.rag, "retrieve"):
                    result = self.rag.retrieve(
                        query=query,
                        category="billing",
                    )
                    return result

                if hasattr(self.rag, "search"):
                    return self.rag.search(
                        query=query,
                        intent="billing",
                    )

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
            from backend.app.rag import rag_service

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

    def _requires_customer_data(
        self,
        query: str,
    ) -> bool:
        return self._select_billing_tool(query) is not None

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
            if self.gemini is not None:
                if hasattr(self.gemini, "generate"):
                    response = self.gemini.generate(
                        prompt=prompt,
                        context=context,
                    )

                    if hasattr(response, "__await__"):
                        response = await response

                    if isinstance(response, dict):
                        response = response.get("response")

                    if response and str(response).strip():
                        return str(response).strip()

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

        return self._build_fallback_response(
            query=query,
            rag_context=rag_context,
            billing_data=billing_data,
        )

    # ==========================================================
    # FALLBACK RESPONSE
    # ==========================================================

    @staticmethod
    def _build_fallback_response(
        query: str,
        rag_context: Any,
        billing_data: Any,
    ) -> str:
        if isinstance(billing_data, dict):
            if billing_data.get("requires_customer_id"):
                return "Please provide your customer ID so I can check your billing details."

            if not billing_data.get("success", False):
                return (
                    billing_data.get("message")
                    or "I could not find billing information for that customer."
                )

            data = billing_data.get("data")

            if isinstance(data, dict):
                bill = data.get("data") if isinstance(data.get("data"), dict) else data
                amount = bill.get("amount") or bill.get("bill_amount")
                due_date = bill.get("due_date") or bill.get("bill_due_date")
                bill_date = bill.get("bill_date")
                status = bill.get("status") or bill.get("payment_status")
                bill_id = bill.get("bill_id") or bill.get("invoice_id")

                details = []
                if amount is not None:
                    details.append(f"amount is {amount}")
                if due_date:
                    details.append(f"due date is {due_date}")
                if status:
                    details.append(f"status is {status}")
                if bill_date:
                    details.append(f"bill date is {bill_date}")

                if details:
                    prefix = f"For bill {bill_id}, the " if bill_id else "Your current bill "
                    return prefix + ", ".join(details) + "."

                message = data.get("message")
                if message:
                    return message

            if isinstance(data, list):
                return f"I found {len(data)} billing record(s) for your account."

        rag_answer = build_response_from_rag(rag_context)
        if rag_answer:
            return rag_answer

        if "bill" in query.lower():
            return "I can help with billing, but I need a valid customer ID to look up account-specific bill details."

        return "I can help with billing questions. Please share your customer ID or ask about your current bill."

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
            "confidence": 0.0,
            "tool_used": None,
            "tool_result": None,
            "rag_context": None,
            "requires_customer_id": False,
        }


# =============================================================
# SHARED BILLING AGENT INSTANCE
# =============================================================

billing_agent = BillingAgent()
