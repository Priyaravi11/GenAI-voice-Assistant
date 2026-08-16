from typing import Any, Dict, Optional


# ============================================================
# NETWORK TOOLS
# ============================================================

from backend.tools.network_tool import (
    get_network_status,
    get_network_issue,
    get_resolution_time,
    check_area_service,
    get_network_details,
)


class TechnicalAgent:
    """
    Technical Agent

    Responsible for handling customer queries related to:
    - Network status
    - Network issues
    - Network outages
    - Service availability
    - Resolution time
    - Network details

    FastAPI is NOT handled here.
    FastAPI routes will be integrated later by the team.
    """

    def __init__(self, rag: Any, tools: Any, gemini: Any):
        """
        Common agent interface.

        Args:
            rag:
                RAG system used for general technical knowledge.

            tools:
                Tool registry/container.
                The actual network functions are imported directly
                from network_tool.py.

            gemini:
                Gemini/LLM interface used for generating the
                final natural-language response.
        """

        self.rag = rag
        self.tools = tools
        self.gemini = gemini

    # ========================================================
    # MAIN HANDLER
    # ========================================================

    async def handle(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for the Technical Agent.

        Args:
            query:
                User's technical/network-related question.

            context:
                Conversation context.

        Returns:
            Structured response for the orchestrator.
        """

        customer_id: Optional[str] = context.get("customer_id")

        language: str = context.get(
            "language",
            "English"
        )

        # ----------------------------------------------------
        # Detect area from context
        # ----------------------------------------------------

        area = context.get("area")

        # ----------------------------------------------------
        # If area is not available in context,
        # try to extract it from the query.
        # ----------------------------------------------------

        if not area:
            area = self._extract_area(query)

        # ----------------------------------------------------
        # Decide whether query needs RAG
        # ----------------------------------------------------

        needs_rag = self._requires_general_technical_knowledge(
            query
        )

        # ----------------------------------------------------
        # Decide which network tool is required
        # ----------------------------------------------------

        tool_name = self._select_network_tool(query)

        rag_context = []
        tool_data = None

        # ====================================================
        # STEP 1: RAG
        # ====================================================

        if needs_rag:

            rag_context = await self._query_technical_rag(
                query
            )

        # ====================================================
        # STEP 2: NETWORK TOOL
        # ====================================================

        if tool_name:

            if not area:

                tool_data = {
                    "success": False,
                    "message": (
                        "Area is required to retrieve "
                        "network information."
                    )
                }

            else:

                tool_data = await self._execute_network_tool(
                    tool_name=tool_name,
                    area=area,
                    customer_id=customer_id,
                    query=query,
                )

        # ====================================================
        # STEP 3: GENERATE RESPONSE
        # ====================================================

        response_text = await self._generate_response(
            query=query,
            language=language,
            rag_context=rag_context,
            tool_data=tool_data,
            context=context,
        )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {
            "agent": "technical",
            "used_rag": bool(rag_context),
            "used_tool": tool_data is not None,
            "tool_name": tool_name,
            "rag_context": rag_context,
            "tool_data": tool_data,
            "response": response_text,
        }

    # ========================================================
    # INTENT DETECTION
    # ========================================================

    def _requires_general_technical_knowledge(
        self,
        query: str
    ) -> bool:
        """
        Determine whether the query requires general
        technical knowledge from RAG.
        """

        q = query.lower()

        general_keywords = [
            "why is 5g slow",
            "why is my 5g slow",
            "why does network",
            "why is network",
            "how to fix",
            "how can i fix",
            "what causes",
            "troubleshoot",
            "troubleshooting",
            "improve signal",
            "signal strength",
            "internet slow",
            "network slow",
            "5g slow",
            "4g slow",
        ]

        return any(
            keyword in q
            for keyword in general_keywords
        )

    # ========================================================
    # NETWORK TOOL SELECTION
    # ========================================================

    def _select_network_tool(
        self,
        query: str
    ) -> Optional[str]:
        """
        Select the appropriate network tool based on
        the user's query.

        Returns:
            Tool function name or None.
        """

        q = query.lower()

        # ----------------------------------------------------
        # Resolution time
        # ----------------------------------------------------

        resolution_keywords = [
            "when will",
            "when will it be fixed",
            "when will network",
            "how long",
            "how long will",
            "resolution",
            "resolved",
            "fix time",
            "repair time",
            "estimated time",
            "eta",
        ]

        if any(
            keyword in q
            for keyword in resolution_keywords
        ):
            return "get_resolution_time"

        # ----------------------------------------------------
        # Network issue
        # ----------------------------------------------------

        issue_keywords = [
            "issue",
            "problem",
            "outage",
            "what is wrong",
            "network problem",
            "network issue",
            "reason for outage",
        ]

        if any(
            keyword in q
            for keyword in issue_keywords
        ):
            return "get_network_issue"

        # ----------------------------------------------------
        # Service availability
        # ----------------------------------------------------

        service_keywords = [
            "service available",
            "service availability",
            "is service available",
            "can i use network",
            "is network available",
            "coverage",
            "available in my area",
            "works in my area",
        ]

        if any(
            keyword in q
            for keyword in service_keywords
        ):
            return "check_area_service"

        # ----------------------------------------------------
        # Complete network information
        # ----------------------------------------------------

        details_keywords = [
            "network details",
            "complete network",
            "full network",
            "tell me everything",
            "all network information",
        ]

        if any(
            keyword in q
            for keyword in details_keywords
        ):
            return "get_network_details"

        # ----------------------------------------------------
        # Network status
        # ----------------------------------------------------

        status_keywords = [
            "network status",
            "network working",
            "is network working",
            "network down",
            "is network down",
            "no signal",
            "no internet",
            "internet not working",
            "network not working",
            "is there an outage",
            "outage in my area",
            "current network",
        ]

        if any(
            keyword in q
            for keyword in status_keywords
        ):
            return "get_network_status"

        # ----------------------------------------------------
        # If query is clearly about user's network,
        # use network status as default.
        # ----------------------------------------------------

        personal_network_keywords = [
            "my network",
            "my internet",
            "my signal",
            "my connection",
            "my 4g",
            "my 5g",
        ]

        if any(
            keyword in q
            for keyword in personal_network_keywords
        ):
            return "get_network_status"

        return None

    # ========================================================
    # AREA EXTRACTION
    # ========================================================

    def _extract_area(
        self,
        query: str
    ) -> Optional[str]:
        """
        Basic area extraction.

        This is intentionally simple for now.

        The preferred source of area is the conversation
        context:

            context["area"]

        Later, the orchestrator/LLM can provide a reliable
        extracted area.
        """

        # ----------------------------------------------------
        # No automatic guessing of arbitrary locations.
        # ----------------------------------------------------
        #
        # Returning None is safer than sending an incorrect
        # location to the Network Tool.
        #

        return None

    # ========================================================
    # EXECUTE NETWORK TOOL
    # ========================================================

    async def _execute_network_tool(
        self,
        tool_name: str,
        area: str,
        customer_id: Optional[str],
        query: str,
    ) -> Dict[str, Any]:
        """
        Execute one of the actual Network Tool functions.

        IMPORTANT:
        These are the real functions from network_tool.py.
        """

        try:

            # ------------------------------------------------
            # Network Status
            # ------------------------------------------------

            if tool_name == "get_network_status":

                return get_network_status(area)

            # ------------------------------------------------
            # Network Issue
            # ------------------------------------------------

            if tool_name == "get_network_issue":

                return get_network_issue(area)

            # ------------------------------------------------
            # Resolution Time
            # ------------------------------------------------

            if tool_name == "get_resolution_time":

                return get_resolution_time(area)

            # ------------------------------------------------
            # Area Service
            # ------------------------------------------------

            if tool_name == "check_area_service":

                return check_area_service(area)

            # ------------------------------------------------
            # Network Details
            # ------------------------------------------------

            if tool_name == "get_network_details":

                return get_network_details(area)

            # ------------------------------------------------
            # Unknown tool
            # ------------------------------------------------

            return {
                "success": False,
                "area": area,
                "message": (
                    f"Unknown network tool: {tool_name}"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "area": area,
                "message": (
                    "Failed to execute network tool"
                ),
                "error": str(e)
            }

    # ========================================================
    # RAG
    # ========================================================

    async def _query_technical_rag(
        self,
        query: str
    ) -> list:
        """
        Query the technical RAG system.

        This supports different possible RAG interfaces
        without hardcoding a fake result.
        """

        if self.rag is None:
            return []

        try:

            # ------------------------------------------------
            # Preferred interface
            # ------------------------------------------------

            if hasattr(self.rag, "query"):

                result = self.rag.query(
                    query,
                    category="technical"
                )

                if hasattr(result, "__await__"):
                    result = await result

                return result or []

            return []

        except Exception:

            return []

    # ========================================================
    # GEMINI RESPONSE
    # ========================================================

    async def _generate_response(
        self,
        query: str,
        language: str,
        rag_context: list,
        tool_data: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        Generate the final response.

        If Gemini is not connected yet, a clean fallback
        response is returned.

        This avoids mock responses.
        """

        # ----------------------------------------------------
        # If Gemini is available
        # ----------------------------------------------------

        if self.gemini is not None:

            try:

                prompt = self._build_prompt(
                    query=query,
                    language=language,
                    rag_context=rag_context,
                    tool_data=tool_data,
                )

                if hasattr(self.gemini, "generate"):

                    result = self.gemini.generate(
                        prompt=prompt,
                        context=context,
                    )

                    if hasattr(result, "__await__"):
                        result = await result

                    if result:
                        return str(result)

            except Exception:
                pass

        # ----------------------------------------------------
        # Fallback response
        # ----------------------------------------------------

        return self._build_fallback_response(
            tool_data=tool_data,
            rag_context=rag_context,
            language=language,
        )

    # ========================================================
    # PROMPT BUILDER
    # ========================================================

    def _build_prompt(
        self,
        query: str,
        language: str,
        rag_context: list,
        tool_data: Optional[Dict[str, Any]],
    ) -> str:
        """
        Build the prompt passed to Gemini.
        """

        return f"""
You are a telecom technical support assistant.

Answer the customer's question clearly and accurately.

Customer language:
{language}

Customer question:
{query}

Live network tool result:
{tool_data}

Technical knowledge from RAG:
{rag_context}

Rules:
1. Do not invent network information.
2. Use the live network tool result when available.
3. Use RAG information for general technical explanations.
4. If information is unavailable, clearly say so.
5. Respond in the customer's requested language.
6. Keep the answer helpful and concise.
"""

    # ========================================================
    # FALLBACK RESPONSE
    # ========================================================

    def _build_fallback_response(
        self,
        tool_data: Optional[Dict[str, Any]],
        rag_context: list,
        language: str,
    ) -> str:
        """
        Generate a basic response when Gemini is unavailable.
        """

        # ----------------------------------------------------
        # Tool result available
        # ----------------------------------------------------

        if tool_data:

            if not tool_data.get("success"):

                return tool_data.get(
                    "message",
                    "Unable to retrieve network information."
                )

            data = tool_data.get(
                "data",
                {}
            )

            message = tool_data.get(
                "message",
                "Network information retrieved successfully."
            )

            # Basic readable response
            if isinstance(data, dict):

                details = []

                for key, value in data.items():

                    if value is not None:

                        formatted_key = key.replace(
                            "_",
                            " "
                        ).title()

                        details.append(
                            f"{formatted_key}: {value}"
                        )

                if details:

                    return (
                        f"{message}\n"
                        + "\n".join(details)
                    )

            return message

        # ----------------------------------------------------
        # RAG result available
        # ----------------------------------------------------

        if rag_context:

            first_result = rag_context[0]

            if isinstance(first_result, dict):

                content = first_result.get(
                    "content"
                )

                if content:
                    return str(content)

            return str(first_result)

        # ----------------------------------------------------
        # Nothing available
        # ----------------------------------------------------

        return (
            "I couldn't find specific network information "
            "for your request."
        )