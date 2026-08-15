from typing import Any, Dict, Optional


class PaymentAgent:
    """
    Agent responsible for handling payment-related customer queries.
    Follows the common agent interface: __init__(rag, tools, gemini) and
    async handle(query, context) -> dict.
    """

    def __init__(self, rag: Any, tools: Any, gemini: Any):
        """
        Args:
            rag: RAG interface exposing something like
                 rag.query(query: str, category: str) -> list[dict]
                 # TODO: PLACEHOLDER - confirm actual method name/signature
                 once rag.py is finalized.
            tools: Tools registry/container exposing payment_tool, e.g.
                   tools.payment_tool.get_payment_status(customer_id, ...)
                   # TODO: PLACEHOLDER - confirm actual tool interface
                   once tools/payment_tool.py is finalized.
            gemini: Gemini wrapper exposing something like
                    gemini.generate(prompt: str, context: dict) -> str
                    # TODO: PLACEHOLDER - confirm actual method name/signature
                    once gemini.py is finalized.
        """
        self.rag = rag
        self.tools = tools
        self.gemini = gemini

    async def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point called by the orchestrator.

        Args:
            query: The user's query (already language-detected/normalized
                   upstream if applicable; this agent does not assume English).
            context: Conversation context from context.py, expected to look
                      roughly like:
                      {
                          "customer_id": "...",
                          "language": "Tamil",
                          "conversation_id": "abc123",
                          "history": [...],
                          "current_agent": "payment"
                      }

        Returns:
            Structured result dict for the orchestrator, e.g.:
            {
                "agent": "payment",
                "used_rag": bool,
                "used_tool": bool,
                "rag_context": [...],
                "tool_data": {...} or None,
                "response": "final natural-language response",
            }
        """
        customer_id: Optional[str] = context.get("customer_id")
        language: str = context.get("language", "English")

        needs_live_data = self._requires_customer_specific_data(query)

        rag_context = []
        tool_data = None

        # ---------------------------------------------------------
        # Step 1: General/static payment knowledge via RAG
        # (e.g. "Why did my payment fail?", "What is the refund policy?")
        # ---------------------------------------------------------
        if self._requires_general_knowledge(query):
            rag_context = await self._query_payment_rag(query)

        # ---------------------------------------------------------
        # Step 2: Live/customer-specific data via Payment Tool
        # (e.g. "Was MY payment successful?", "When will MY refund arrive?")
        # ---------------------------------------------------------
        if needs_live_data:
            tool_data = await self._query_payment_tool(customer_id, query, context)

        # ---------------------------------------------------------
        # Step 3: Generate final response via Gemini
        # ---------------------------------------------------------
        response_text = await self._generate_response(
            query=query,
            language=language,
            rag_context=rag_context,
            tool_data=tool_data,
            context=context,
        )

        return {
            "agent": "payment",
            "used_rag": bool(rag_context),
            "used_tool": tool_data is not None,
            "rag_context": rag_context,
            "tool_data": tool_data,
            "response": response_text,
        }

    # ------------------------------------------------------------
    # Intent helpers
    # ------------------------------------------------------------

    def _requires_general_knowledge(self, query: str) -> bool:
        """
        Decide whether this query needs general/static payment knowledge.

        # TODO: PLACEHOLDER - naive keyword heuristic for now. Once an
        # actual intent classifier / Gemini-based intent step is agreed
        # upon (possibly shared with other agents), replace this with
        # that shared utility instead of duplicating keyword logic here.
        """
        general_keywords = [
            "policy", "refund policy", "why does payment fail",
            "how long does a refund take", "what is a refund",
            "payment methods", "how to pay",
        ]
        q = query.lower()
        return any(kw in q for kw in general_keywords)

    def _requires_customer_specific_data(self, query: str) -> bool:
        """
        Decide whether this query needs live/customer-specific payment data.

        # TODO: PLACEHOLDER - naive keyword heuristic for now, same caveat
        # as above. Words like "my", "was my", etc. are strong signals per
        # the RAG vs Tool rule in the spec.
        """
        live_keywords = [
            "my payment", "my refund", "was my payment",
            "did my payment", "payment failed", "refund status",
            "when will my refund",
        ]
        q = query.lower()
        return any(kw in q for kw in live_keywords)

    # ------------------------------------------------------------
    # RAG / Tool / Gemini calls (all mocked for now)
    # ------------------------------------------------------------

    async def _query_payment_rag(self, query: str) -> list:
        """
        # TODO: PLACEHOLDER - replace with actual rag.py call, e.g.:
        #     return await self.rag.query(query, category="payment")
        """
        mock_result = [
            {
                "source": "payment_faq.md",
                "content": (
                    "[MOCK RAG RESULT] Payments can fail due to insufficient "
                    "balance, bank server issues, or incorrect card details. "
                    "Refunds are typically processed within 5-7 business days."
                ),
            }
        ]
        return mock_result

    async def _query_payment_tool(
        self, customer_id: Optional[str], query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        # TODO: PLACEHOLDER - replace with actual tools/payment_tool.py call, e.g.:
        #     return await self.tools.payment_tool.get_payment_status(
        #         customer_id=customer_id
        #     )
        """
        mock_result = {
            "customer_id": customer_id or "UNKNOWN_MOCK_ID",
            "last_payment_status": "MOCK_FAILED",
            "last_payment_amount": "₹799 (mock)",
            "failure_reason": "MOCK: Bank server timeout",
            "refund_status": "MOCK: Not applicable",
            "refund_eta_days": None,
        }
        return mock_result

    async def _generate_response(
        self,
        query: str,
        language: str,
        rag_context: list,
        tool_data: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        # TODO: PLACEHOLDER - replace with actual gemini.py call, e.g.:
        #     return await self.gemini.generate(
        #         prompt=self._build_prompt(query, rag_context, tool_data),
        #         context=context,
        #         target_language=language,
        #     )
        """
        if tool_data:
            return (
                f"[MOCK GEMINI RESPONSE - lang={language}] "
                f"It looks like your last payment "
                f"({tool_data.get('last_payment_amount')}) status was "
                f"{tool_data.get('last_payment_status')}. "
                f"Reason: {tool_data.get('failure_reason')}."
            )
        if rag_context:
            return (
                f"[MOCK GEMINI RESPONSE - lang={language}] "
                f"{rag_context[0]['content']}"
            )
        return (
            f"[MOCK GEMINI RESPONSE - lang={language}] "
            f"I couldn't determine specific payment details for: '{query}'."
        )