from typing import Any, Dict, Optional

from app.gemini import generate_text

# ============================================================
# NETWORK TOOLS
# ============================================================
# Per backend/app/tools.py's own docstring: "Agents should call
# tools through this file instead of directly depending on
# individual tool modules." So we go through the central
# registry's execute_tool_async() rather than importing
# get_network_status/get_network_issue/etc. from
# tools.network_tool directly. execute_tool_async also already
# handles the sync/async distinction internally (via
# inspect.isawaitable), so we don't need to special-case that
# here either.
# ============================================================

from backend.app.tools import execute_tool_async


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

    # Known network tool names. Used to validate a "required_tool"
    # value coming back from context before trusting/reusing it.
    VALID_TOOLS = {
        "get_network_status",
        "get_network_issue",
        "get_resolution_time",
        "check_area_service",
        "get_network_details",
    }

    def __init__(self, rag: Any, tools: Any, gemini: Any = None):
        """
        Common agent interface.

        Args:
            rag:
                RAG system used for general technical knowledge.

            tools:
                Tool registry/container.
                Network functions are invoked via
                backend.app.tools.execute_tool_async, not
                imported directly.

            gemini:
                Kept for backward compatibility with the common
                agent interface. Response generation now goes
                through app.gemini.generate_text directly, so
                this is no longer required.
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

        language = context.get(
            "language",
            "English",
        )

        # If language is passed as a structured object (e.g.
        # {"primary": "Tamil", "confidence": 0.9}), extract the
        # primary language rather than stringifying the whole dict
        # into the prompt.
        if isinstance(language, dict):
            language = language.get(
                "primary",
                "English",
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
        # Decide which network tool is required.
        #
        # A freshly-detected tool from the CURRENT query always
        # wins. We only fall back to a pending "required_tool"
        # from context (set on a previous turn, e.g. when we asked
        # "what's your area?") when the current message doesn't
        # match any tool intent on its own -- i.e. it's plausibly
        # just the area answer ("Chennai"), not a new request.
        #
        # This avoids the opposite bug: if the user answers the
        # area question with a message that itself states a new,
        # different intent ("actually, when will it be resolved?"),
        # that new intent should not be silently overridden by a
        # stale pending tool.
        # ----------------------------------------------------

        selected_tool = self._select_network_tool(query)
        pending_tool = context.get("required_tool")

        if selected_tool:
            tool_name = selected_tool
        elif pending_tool in self.VALID_TOOLS:
            tool_name = pending_tool
        else:
            tool_name = None

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

                return {
                    "agent": "technical",
                    "response": (
                        "Sure, I can check the network information. "
                        "Could you please provide your area or location?"
                    ),
                    "used_rag": bool(rag_context),
                    "used_tool": False,
                    "tool_name": tool_name,
                    "required_tool": tool_name,
                    "rag_context": rag_context,
                    "tool_data": None,
                    "requires_area": True,
                }

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
            "required_tool": tool_name,
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
        Execute a network tool through the central tool registry
        (backend/app/tools.py: execute_tool_async), rather than
        importing/dispatching individual network_tool functions
        directly.

        NOTE: network_tool.py's functions take only `area` -- no
        `customer_id` -- so it isn't forwarded to the tool call.
        customer_id is still accepted as a param here in case a
        future tool in this agent needs it.
        """

        try:

            return await execute_tool_async(
                tool_name,
                area=area,
            )

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

        NOTE: left on the self.rag.query(...) interface. Don't
        switch this to a centralized rag_service until you've
        confirmed its actual method signature in
        backend/app/rag.py -- guessing here risks a silent
        integration break.
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
        Generate the final response using app.gemini.generate_text.

        If generation fails, a clean fallback response is
        returned. This avoids mock responses.
        """

        try:

            history = context.get("history", [])

            prompt = self._build_prompt(
                query=query,
                language=language,
                rag_context=rag_context,
                tool_data=tool_data,
                history=history,
            )

            result = await generate_text(prompt)

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
        history: Any,
    ) -> str:
        """
        Build the prompt passed to Gemini.
        """

        return f"""
You are a telecom technical support assistant.

Answer the customer's question clearly and accurately.

Customer language:
{language}

Conversation history:
{history}

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
4. Use conversation history to understand context (e.g. an area
   mentioned in a follow-up turn answering a previous question).
5. If information is unavailable, clearly say so.
6. Respond in the customer's requested language.
7. Keep the answer helpful and concise.
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