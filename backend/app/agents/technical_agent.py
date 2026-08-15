from typing import Any, Dict, Optional


class TechnicalAgent:
    """
    Agent responsible for handling technical/network-related customer queries.
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
            tools: Tools registry/container exposing network_tool, e.g.
                   tools.network_tool.check_status(customer_id, area, ...)
                   # TODO: PLACEHOLDER - confirm actual tool interface
                   once tools/network_tool.py is finalized.
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
                          "current_agent": "technical"
                      }

        Returns:
            Structured result dict for the orchestrator, e.g.:
            {
                "agent": "technical",
                "used_rag": bool,
                "used_tool": bool,
                "rag_context": [...],
                "tool_data": {...} or None,
                "response": "final natural-language response",
            }
        """
        customer_id: Optional[str] = context.get("customer_id")
        language: str = context.get("language", "English")

        # Per the spec's flow diagram, Technical Agent typically uses
        # RAG + Network Tool together rather than one-or-the-other, but
        # we still gate on intent to avoid unnecessary tool calls.
        needs_general_knowledge = self._requires_general_knowledge(query)
        needs_live_network_check = self._requires_live_network_data(query)

        rag_context = []
        tool_data = None

        # ---------------------------------------------------------
        # Step 1: General technical knowledge via RAG
        # (e.g. "Why can 5G become slow?", basic troubleshooting steps)
        # ---------------------------------------------------------
        if needs_general_knowledge:
            rag_context = await self._query_technical_rag(query)

        # ---------------------------------------------------------
        # Step 2: Live network status via Network Tool
        # (e.g. "My internet isn't working", "Is there an outage in my area?")
        # ---------------------------------------------------------
        if needs_live_network_check:
            tool_data = await self._query_network_tool(customer_id, query, context)

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
            "agent": "technical",
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
        # TODO: PLACEHOLDER - naive keyword heuristic for now. Replace with
        # shared intent classification utility once available.
        """
        general_keywords = [
            "why is 5g slow", "why does network", "how to fix",
            "what causes", "troubleshoot", "improve signal",
        ]
        q = query.lower()
        return any(kw in q for kw in general_keywords)

    def _requires_live_network_data(self, query: str) -> bool:
        """
        # TODO: PLACEHOLDER - naive keyword heuristic for now. Queries
        # about "my" connection/area or explicit outage checks should
        # hit the live Network Tool per the RAG vs Tool rule.
        """
        live_keywords = [
            "not working", "no signal", "no internet", "network down",
            "outage", "my network", "my internet", "my 5g",
            "is there an outage",
        ]
        q = query.lower()
        return any(kw in q for kw in live_keywords)

    # ------------------------------------------------------------
    # RAG / Tool / Gemini calls (all mocked for now)
    # ------------------------------------------------------------

    async def _query_technical_rag(self, query: str) -> list:
        """
        # TODO: PLACEHOLDER - replace with actual rag.py call, e.g.:
        #     return await self.rag.query(query, category="technical")
        """
        mock_result = [
            {
                "source": "technical_faq.md",
                "content": (
                    "[MOCK RAG RESULT] 5G speeds can drop due to network "
                    "congestion, poor signal strength, device compatibility, "
                    "or ongoing maintenance in your area."
                ),
            }
        ]
        return mock_result

    async def _query_network_tool(
        self, customer_id: Optional[str], query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        # TODO: PLACEHOLDER - replace with actual tools/network_tool.py call, e.g.:
        #     return await self.tools.network_tool.check_status(
        #         customer_id=customer_id
        #     )
        """
        mock_result = {
            "customer_id": customer_id or "UNKNOWN_MOCK_ID",
            "network_status": "MOCK_OUTAGE_DETECTED",
            "area": "MOCK_AREA",
            "estimated_resolution": "MOCK: 2 hours",
            "signal_strength": "MOCK: Weak",
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
                f"Network status for your area: {tool_data.get('network_status')}. "
                f"Estimated resolution: {tool_data.get('estimated_resolution')}."
            )
        if rag_context:
            return (
                f"[MOCK GEMINI RESPONSE - lang={language}] "
                f"{rag_context[0]['content']}"
            )
        return (
            f"[MOCK GEMINI RESPONSE - lang={language}] "
            f"I couldn't determine specific network details for: '{query}'."
        )