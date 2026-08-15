from typing import Any, Dict, Optional


class PlansAgent:
    """
    Agent responsible for handling plan-related customer queries.
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
            tools: Tools registry/container exposing plans_tool, e.g.
                   tools.plans_tool.get_current_plan(customer_id, ...)
                   tools.plans_tool.check_upgrade_eligibility(customer_id, ...)
                   # TODO: PLACEHOLDER - confirm actual tool interface
                   once tools/plans_tool.py is finalized.
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
            query: The user's query.
            context: Conversation context from context.py, expected to look
                      roughly like:
                      {
                          "customer_id": "...",
                          "language": "Tamil",
                          "conversation_id": "abc123",
                          "history": [...],
                          "current_agent": "plans"
                      }

        Returns:
            Structured result dict for the orchestrator, e.g.:
            {
                "agent": "plans",
                "used_rag": bool,
                "used_tool": bool,
                "rag_context": [...],
                "tool_data": {...} or None,
                "response": "final natural-language response",
            }
        """
        customer_id: Optional[str] = context.get("customer_id")
        language: str = context.get("language", "English")

        # Per the spec's flow diagram, Plans Agent may use RAG and Tool
        # together (Plans RAG + Plans Tool when customer-specific info
        # or action is required).
        needs_general_knowledge = self._requires_general_knowledge(query)
        needs_customer_specific_data = self._requires_customer_specific_data(query)

        rag_context = []
        tool_data = None

        # ---------------------------------------------------------
        # Step 1: General plan knowledge via RAG
        # (e.g. "What plans are available?", "Which plan has unlimited data?")
        # ---------------------------------------------------------
        if needs_general_knowledge:
            rag_context = await self._query_plans_rag(query)

        # ---------------------------------------------------------
        # Step 2: Customer-specific plan info/action via Plans Tool
        # (e.g. "What is MY current plan?", "Can I upgrade my plan?")
        # ---------------------------------------------------------
        if needs_customer_specific_data:
            tool_data = await self._query_plans_tool(customer_id, query, context)

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
            "agent": "plans",
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
        Decide whether this query needs general/static plan knowledge.

        # TODO: PLACEHOLDER - naive keyword heuristic for now. Once an
        # actual intent classifier / Gemini-based intent step is agreed
        # upon (possibly shared with other agents), replace this with
        # that shared utility instead of duplicating keyword logic here.
        """
        general_keywords = [
            "what plans", "which plan", "how much is the", "compare",
            "plan details", "plan features", "unlimited data",
            "available plans",
        ]
        q = query.lower()
        return any(kw in q for kw in general_keywords)

    def _requires_customer_specific_data(self, query: str) -> bool:
        """
        Decide whether this query needs customer-specific plan info/action.

        # TODO: PLACEHOLDER - naive keyword heuristic for now, same caveat
        # as above. Words like "my", "upgrade", "current plan" are strong
        # signals per the RAG vs Tool rule in the spec.
        """
        live_keywords = [
            "my plan", "my current plan", "can i upgrade", "upgrade my",
            "downgrade my", "switch my plan", "what is my plan",
        ]
        q = query.lower()
        return any(kw in q for kw in live_keywords)

    # ------------------------------------------------------------
    # RAG / Tool / Gemini calls (all mocked for now)
    # ------------------------------------------------------------

    async def _query_plans_rag(self, query: str) -> list:
        """
        # TODO: PLACEHOLDER - replace with actual rag.py call, e.g.:
        #     return await self.rag.query(query, category="plans")
        """
        mock_result = [
            {
                "source": "plans_faq.md",
                "content": (
                    "[MOCK RAG RESULT] We offer Basic, Standard, and Premium "
                    "plans. The Premium plan includes unlimited 5G data, "
                    "OTT subscriptions, and international roaming add-ons."
                ),
            }
        ]
        return mock_result

    async def _query_plans_tool(
        self, customer_id: Optional[str], query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        # TODO: PLACEHOLDER - replace with actual tools/plans_tool.py call, e.g.:
        #     return await self.tools.plans_tool.get_current_plan(
        #         customer_id=customer_id
        #     )
        # or, for upgrade queries:
        #     return await self.tools.plans_tool.check_upgrade_eligibility(
        #         customer_id=customer_id
        #     )
        """
        mock_result = {
            "customer_id": customer_id or "UNKNOWN_MOCK_ID",
            "current_plan": "MOCK_Standard_499",
            "plan_expiry": "MOCK: 2026-09-10",
            "upgrade_eligible": True,
            "recommended_upgrade": "MOCK_Premium_899",
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
                f"Your current plan is {tool_data.get('current_plan')}, "
                f"expiring on {tool_data.get('plan_expiry')}. "
                f"Upgrade eligible: {tool_data.get('upgrade_eligible')} "
                f"(suggested: {tool_data.get('recommended_upgrade')})."
            )
        if rag_context:
            return (
                f"[MOCK GEMINI RESPONSE - lang={language}] "
                f"{rag_context[0]['content']}"
            )
        return (
            f"[MOCK GEMINI RESPONSE - lang={language}] "
            f"I couldn't determine specific plan details for: '{query}'."
        )