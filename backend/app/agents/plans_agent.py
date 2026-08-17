from typing import Any, Dict, List, Optional

from app.gemini import generate_text
from app.rag import rag_service

# ============================================================
# PLAN TOOLS
# ============================================================
# NOTE: tools/plans_tool.py currently only implements these
# four functions. get_current_plan and get_available_plans
# are NOT yet defined there, so they are intentionally not
# imported here (importing them would raise ImportError and
# crash the agent). See _execute_plan_tool() below for how
# those two intents are handled in the meantime.

from tools.plans_tool import (
    get_plan_details,
    compare_plans,
    find_plans,
    get_plan_change_info,
)


# ============================================================
# TOOL / INTENT CONSTANTS
# ============================================================

VALID_TOOLS = {
    "get_current_plan",
    "get_plan_details",
    "get_available_plans",
    "compare_plans",
    "find_plans",
    "get_plan_change_info",
}

# Tools not yet implemented in tools/plans_tool.py. Detected as
# intents (so required_tool / customer-ID flows still work) but
# executed as a graceful "not available" result instead of a
# real call.
_NOT_YET_IMPLEMENTED_TOOLS = {
    "get_current_plan",
    "get_available_plans",
}

CUSTOMER_ID_REQUIRED_TOOLS = {
    "get_current_plan",
    "get_plan_change_info",
}

_CUSTOMER_ID_PROMPTS = {
    "get_current_plan": (
        "Sure, I can check your current plan. "
        "Could you please provide your customer ID?"
    ),
    "get_plan_change_info": (
        "Sure, I can help with changing your plan. "
        "Could you please provide your customer ID?"
    ),
}


class PlansAgent:
    """
    Plans Agent

    Responsible for handling customer queries related to:
    - Current subscribed plan
    - Plan details
    - Available plans
    - Plan comparison
    - Finding plans based on requirements
    - Plan upgrades/downgrades/change information

    FastAPI is NOT handled here.
    FastAPI routes will be integrated later.
    """

    def __init__(
        self,
        rag: Any,
        tools: Any,
        gemini: Any = None
    ):
        """
        Common agent interface.

        Args:
            rag:
                Kept for backward compatibility with the common
                agent interface. RAG retrieval now goes through
                the centralized app.rag.rag_service directly, so
                this is no longer required.

            tools:
                Tool registry/container.

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
        Main entry point for the Plans Agent.
        """

        customer_id: Optional[str] = context.get("customer_id")

        language: str = context.get("language", "English")

        if isinstance(language, dict):
            language = language.get("primary", "English")

        history = context.get("history", [])

        # ----------------------------------------------------
        # Detect required plan tool.
        #
        # If the orchestrator persisted a required_tool from a
        # previous turn (e.g. we already asked for a customer
        # ID), reuse it instead of re-detecting intent from the
        # current query — a follow-up like "C251" would not
        # match any intent keywords on its own.
        # ----------------------------------------------------

        pending_tool = context.get("required_tool")

        if pending_tool in VALID_TOOLS:
            tool_name = pending_tool
        else:
            tool_name = self._select_plan_tool(query)

        # ----------------------------------------------------
        # Customer ID gate (current plan / plan change only)
        # ----------------------------------------------------

        if tool_name in CUSTOMER_ID_REQUIRED_TOOLS and not customer_id:

            return {
                "agent": "plans",
                "response": _CUSTOMER_ID_PROMPTS[tool_name],
                "success": False,
                "requires_customer_id": True,
                "required_tool": tool_name,
                "tool_used": None,
            }

        # ----------------------------------------------------
        # Check whether general plan knowledge is needed
        # ----------------------------------------------------

        needs_rag = self._requires_general_plan_knowledge(query)

        rag_context: list = []
        tool_data: Optional[Dict[str, Any]] = None

        # ====================================================
        # STEP 1: RAG (centralized rag_service, synchronous)
        # ====================================================

        if needs_rag:
            rag_context = self._query_plan_rag(
                query=query,
                context=context,
                language=language,
            )

        # ====================================================
        # STEP 2: PLAN TOOL (synchronous)
        # ====================================================

        if tool_name:

            tool_data = self._execute_plan_tool(
                tool_name=tool_name,
                query=query,
                customer_id=customer_id,
                context=context,
            )

        # ====================================================
        # STEP 3: GEMINI (async)
        # ====================================================

        response_text = await self._generate_response(
            query=query,
            language=language,
            rag_context=rag_context,
            tool_data=tool_data,
            history=history,
        )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {
            "agent": "plans",
            "used_rag": bool(rag_context),
            "used_tool": tool_data is not None,
            "tool_name": tool_name,
            "required_tool": tool_name,
            "rag_context": rag_context,
            "tool_data": tool_data,
            "response": response_text,
        }

    # ========================================================
    # PLAN INTENT DETECTION
    # ========================================================

    def _select_plan_tool(
        self,
        query: str
    ) -> Optional[str]:
        """
        Select the correct Plans Tool function.

        Returns:
            Actual tool function name or None.
        """

        q = query.lower()

        # ====================================================
        # CURRENT PLAN
        # ====================================================

        current_plan_keywords = [
            "my current plan",
            "current plan",
            "which plan am i using",
            "what plan am i using",
            "my plan",
            "my subscribed plan",
            "subscribed plan",
            "my subscription plan",
        ]

        if any(
            keyword in q
            for keyword in current_plan_keywords
        ):
            return "get_current_plan"

        # ====================================================
        # PLAN CHANGE
        # ====================================================

        plan_change_keywords = [
            "change my plan",
            "change plan",
            "switch plan",
            "upgrade my plan",
            "upgrade plan",
            "downgrade my plan",
            "downgrade plan",
            "move to another plan",
            "change to plan",
            "switch to plan",
        ]

        if any(
            keyword in q
            for keyword in plan_change_keywords
        ):
            return "get_plan_change_info"

        # ====================================================
        # COMPARE PLANS
        # ====================================================

        compare_keywords = [
            "compare plans",
            "compare these plans",
            "compare two plans",
            "difference between plans",
            "difference between these plans",
            "which is better",
            "plan comparison",
            "compare",
        ]

        if any(
            keyword in q
            for keyword in compare_keywords
        ):
            return "compare_plans"

        # ====================================================
        # FIND PLANS
        # ====================================================

        find_keywords = [
            "find a plan",
            "find plans",
            "find me a plan",
            "suggest a plan",
            "recommend a plan",
            "recommend plans",
            "best plan for me",
            "best plan",
            "cheapest plan",
            "affordable plan",
            "plan under",
            "plan below",
            "plan with",
        ]

        if any(
            keyword in q
            for keyword in find_keywords
        ):
            return "find_plans"

        # ====================================================
        # AVAILABLE PLANS
        # ====================================================

        available_keywords = [
            "available plans",
            "available plan",
            "what plans are available",
            "what plans do you have",
            "plans available",
            "show me plans",
            "list plans",
            "all plans",
            "plans offered",
        ]

        if any(
            keyword in q
            for keyword in available_keywords
        ):
            return "get_available_plans"

        # ====================================================
        # PLAN DETAILS
        # ====================================================

        details_keywords = [
            "plan details",
            "details of plan",
            "details about plan",
            "tell me about plan",
            "information about plan",
            "plan information",
            "what does this plan include",
            "what is included in plan",
        ]

        if any(
            keyword in q
            for keyword in details_keywords
        ):
            return "get_plan_details"

        return None

    # ========================================================
    # GENERAL PLAN KNOWLEDGE
    # ========================================================

    def _requires_general_plan_knowledge(
        self,
        query: str
    ) -> bool:
        """
        Determine whether the query needs general
        plan-related knowledge from RAG.
        """

        q = query.lower()

        keywords = [
            "what is a prepaid plan",
            "what is a postpaid plan",
            "what is roaming",
            "what is data rollover",
            "what is unlimited data",
            "how does roaming work",
            "how do plans work",
            "difference between prepaid and postpaid",
            "what is a family plan",
        ]

        return any(
            keyword in q
            for keyword in keywords
        )

    # ========================================================
    # EXECUTE PLAN TOOL (synchronous — tools are sync)
    # ========================================================

    def _execute_plan_tool(
        self,
        tool_name: str,
        query: str,
        customer_id: Optional[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the actual Plans Tool function.

        IMPORTANT:
        These are the real (synchronous) functions from
        tools/plans_tool.py. Do not await them.
        """

        try:

            # =================================================
            # CURRENT PLAN (not yet implemented in plans_tool.py)
            # =================================================

            if tool_name == "get_current_plan":

                if not customer_id:

                    return {
                        "success": False,
                        "requires_customer_id": True,
                        "message": _CUSTOMER_ID_PROMPTS["get_current_plan"],
                    }

                return self._not_yet_implemented("get_current_plan")

            # =================================================
            # PLAN DETAILS
            # =================================================

            if tool_name == "get_plan_details":

                plan_id = context.get(
                    "plan_id"
                )

                if not plan_id:
                    plan_id = self._extract_plan_id(
                        query
                    )

                if not plan_id:

                    return {
                        "success": False,
                        "message": (
                            "Plan ID is required "
                            "to retrieve plan details."
                        )
                    }

                return get_plan_details(
                    plan_id
                )

            # =================================================
            # AVAILABLE PLANS (not yet implemented in plans_tool.py)
            # =================================================

            if tool_name == "get_available_plans":

                return self._not_yet_implemented("get_available_plans")

            # =================================================
            # COMPARE PLANS
            # =================================================

            if tool_name == "compare_plans":

                plan_ids = self._extract_two_plan_ids(
                    query,
                    context
                )

                if not plan_ids:

                    return {
                        "success": False,
                        "message": (
                            "Two plan IDs are required "
                            "to compare plans."
                        )
                    }

                return compare_plans(
                    plan_ids[0],
                    plan_ids[1]
                )

            # =================================================
            # FIND PLANS
            # =================================================

            if tool_name == "find_plans":

                filters = self._extract_plan_filters(
                    query,
                    context
                )

                return find_plans(
                    max_price=filters.get(
                        "max_price"
                    ),
                    min_data_gb=filters.get(
                        "min_data_gb"
                    ),
                    plan_type=filters.get(
                        "plan_type"
                    ),
                    roaming_required=filters.get(
                        "roaming_required"
                    ),
                )

            # =================================================
            # PLAN CHANGE
            # =================================================

            if tool_name == "get_plan_change_info":

                if not customer_id:

                    return {
                        "success": False,
                        "requires_customer_id": True,
                        "message": _CUSTOMER_ID_PROMPTS["get_plan_change_info"],
                    }

                new_plan_id = context.get(
                    "new_plan_id"
                )

                if not new_plan_id:

                    new_plan_id = self._extract_plan_id(
                        query
                    )

                if not new_plan_id:

                    return {
                        "success": False,
                        "customer_id": customer_id,
                        "message": (
                            "New plan ID is required "
                            "to check plan change information."
                        )
                    }

                return get_plan_change_info(
                    customer_id,
                    new_plan_id
                )

            # =================================================
            # UNKNOWN TOOL
            # =================================================

            return {
                "success": False,
                "message": (
                    f"Unknown plan tool: {tool_name}"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "message": "Failed to execute plan tool",
                "error": str(e)
            }

    @staticmethod
    def _not_yet_implemented(tool_name: str) -> Dict[str, Any]:
        """
        Graceful placeholder for intents whose backing function
        does not exist yet in tools/plans_tool.py. Returns a
        structured failure instead of raising, so the agent
        never crashes on these intents.
        """

        return {
            "success": False,
            "message": (
                "That feature isn't available yet — "
                "please try again later or contact support."
            ),
            "tool_name": tool_name,
        }

    # ========================================================
    # PLAN ID EXTRACTION
    # ========================================================

    def _extract_plan_id(
        self,
        query: str
    ) -> Optional[str]:
        """
        Extract a plan ID from the query.

        Example:
            "Tell me about plan P101"

        returns:
            "P101"
        """

        words = query.replace(
            ",",
            " "
        ).replace(
            ".",
            " "
        ).split()

        for word in words:

            cleaned = word.strip(
                "()[]{}:;!?\"'"
            )

            if cleaned.lower().startswith(
                "plan"
            ):
                continue

            # Typical plan IDs often contain
            # letters followed by numbers.
            if (
                len(cleaned) >= 2
                and any(
                    char.isdigit()
                    for char in cleaned
                )
                and any(
                    char.isalpha()
                    for char in cleaned
                )
            ):
                return cleaned

        return None

    # ========================================================
    # TWO PLAN IDS
    # ========================================================

    def _extract_two_plan_ids(
        self,
        query: str,
        context: Dict[str, Any]
    ):
        """
        Get two plan IDs from context or query.
        """

        plan_id_1 = context.get(
            "plan_id_1"
        )

        plan_id_2 = context.get(
            "plan_id_2"
        )

        if plan_id_1 and plan_id_2:

            return [
                plan_id_1,
                plan_id_2
            ]

        # ----------------------------------------------------
        # Try extracting IDs from query
        # ----------------------------------------------------

        words = query.replace(
            ",",
            " "
        ).replace(
            ".",
            " "
        ).split()

        plan_ids = []

        for word in words:

            cleaned = word.strip(
                "()[]{}:;!?\"'"
            )

            if (
                len(cleaned) >= 2
                and any(
                    char.isdigit()
                    for char in cleaned
                )
                and any(
                    char.isalpha()
                    for char in cleaned
                )
            ):

                if cleaned not in plan_ids:
                    plan_ids.append(cleaned)

        if len(plan_ids) >= 2:

            return [
                plan_ids[0],
                plan_ids[1]
            ]

        return None

    # ========================================================
    # PLAN FILTER EXTRACTION
    # ========================================================

    def _extract_plan_filters(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract plan search filters.

        Supported filters:
        - max_price
        - min_data_gb
        - plan_type
        - roaming_required

        Context values are preferred when available.
        """

        filters = {}

        # ----------------------------------------------------
        # Context values
        # ----------------------------------------------------

        if context.get("max_price") is not None:

            filters["max_price"] = context.get(
                "max_price"
            )

        if context.get("min_data_gb") is not None:

            filters["min_data_gb"] = context.get(
                "min_data_gb"
            )

        if context.get("plan_type") is not None:

            filters["plan_type"] = context.get(
                "plan_type"
            )

        if context.get("roaming_required") is not None:

            filters["roaming_required"] = context.get(
                "roaming_required"
            )

        # ----------------------------------------------------
        # Basic numeric extraction
        # ----------------------------------------------------

        words = query.lower().replace(
            ",",
            " "
        ).split()

        for index, word in enumerate(words):

            cleaned = word.strip(
                "$₹"
            )

            # -----------------------------------------------
            # Price
            # -----------------------------------------------

            if (
                cleaned.isdigit()
                and index > 0
            ):

                previous_word = words[
                    index - 1
                ]

                if previous_word in [
                    "under",
                    "below",
                    "less",
                    "maximum",
                    "max",
                ]:

                    if "max_price" not in filters:

                        filters["max_price"] = float(
                            cleaned
                        )

                # -------------------------------------------
                # Data
                # -------------------------------------------

                if index + 1 < len(words):

                    next_word = words[
                        index + 1
                    ]

                    if next_word in [
                        "gb",
                        "gbs",
                    ]:

                        if previous_word in [
                            "at",
                            "minimum",
                            "min",
                            "above",
                            "more",
                        ]:

                            if "min_data_gb" not in filters:

                                filters[
                                    "min_data_gb"
                                ] = float(
                                    cleaned
                                )

        # ----------------------------------------------------
        # Plan type
        # ----------------------------------------------------

        if "prepaid" in words:

            filters["plan_type"] = "prepaid"

        elif "postpaid" in words:

            filters["plan_type"] = "postpaid"

        # ----------------------------------------------------
        # Roaming
        # ----------------------------------------------------

        if (
            "roaming" in words
            and (
                "required" in words
                or "included" in words
                or "need" in words
            )
        ):

            filters["roaming_required"] = True

        return filters

    # ========================================================
    # RAG (centralized rag_service, synchronous)
    # ========================================================

    def _query_plan_rag(
        self,
        query: str,
        context: Dict[str, Any],
        language: str,
    ) -> list:
        """
        Query plan-related knowledge via the centralized
        RAG service (app.rag.rag_service).

        Uses rag_service.search(), the convenience entry point
        for callers that only have a raw query + light context
        rather than a full NLU payload. rag_service is
        synchronous, so this method is synchronous too — no
        need for an async wrapper.
        """

        try:

            entities: Dict[str, Any] = {}

            for key in (
                "customer_id",
                "plan_id",
                "plan_id_1",
                "plan_id_2",
                "new_plan_id",
            ):
                value = context.get(key)
                if value:
                    entities[key] = value

            result = rag_service.search(
                query=query,
                request_id=str(
                    context.get("request_id", "plans-agent")
                ),
                language=language or "en",
                intent="plans",
                entities=entities,
                sentiment=context.get("sentiment", "neutral"),
                code_switched=bool(
                    context.get("code_switched", False)
                ),
            )

            return result.get("retrieved_context", []) or []

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
        tool_data: Optional[
            Dict[str, Any]
        ],
        history: list,
    ) -> str:
        """
        Generate final natural-language response using
        app.gemini.generate_text.
        """

        try:

            prompt = self._build_prompt(
                query=query,
                language=language,
                rag_context=rag_context,
                tool_data=tool_data,
                history=history,
            )

            result = await generate_text(
                prompt
            )

            if result:

                return str(result)

        except Exception:
            pass

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        return self._build_fallback_response(
            tool_data=tool_data,
            rag_context=rag_context,
        )

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        query: str,
        language: str,
        rag_context: list,
        tool_data: Optional[
            Dict[str, Any]
        ],
        history: list,
    ) -> str:
        """
        Build Gemini prompt.
        """

        return f"""
You are a telecom plans assistant.

Answer the customer's question clearly and accurately.

Customer language:
{language}

Conversation history:
{history}

Customer question:
{query}

Plan tool result:
{tool_data}

Plan knowledge from RAG:
{rag_context}

Rules:
1. Use the plan tool result when available.
2. Do not invent plan prices, benefits, limits, or features.
3. Explain plan comparisons clearly.
4. If the requested plan does not exist, say so.
5. Use the conversation history to understand follow-up questions.
6. Respond in the customer's language; do not mix languages unnecessarily.
7. Keep the answer concise and helpful.
8. Never mention tools, RAG, prompts, or internal implementation details.
"""

    # ========================================================
    # FALLBACK RESPONSE
    # ========================================================

    def _build_fallback_response(
        self,
        tool_data: Optional[
            Dict[str, Any]
        ],
        rag_context: list,
    ) -> str:
        """
        Basic fallback response when Gemini
        is unavailable.
        """

        # ----------------------------------------------------
        # Tool result
        # ----------------------------------------------------

        if tool_data:

            if not tool_data.get(
                "success"
            ):

                return tool_data.get(
                    "message",
                    "Unable to retrieve plan information."
                )

            message = tool_data.get(
                "message",
                "Plan information retrieved successfully."
            )

            data = tool_data.get(
                "data"
            )

            if data is None:

                return message

            # ------------------------------------------------
            # Dictionary result
            # ------------------------------------------------

            if isinstance(
                data,
                dict
            ):

                details = []

                for key, value in data.items():

                    if value is not None:

                        formatted_key = (
                            key.replace(
                                "_",
                                " "
                            ).title()
                        )

                        details.append(
                            f"{formatted_key}: {value}"
                        )

                if details:

                    return (
                        f"{message}\n"
                        + "\n".join(details)
                    )

            # ------------------------------------------------
            # List result
            # ------------------------------------------------

            if isinstance(
                data,
                list
            ):

                return (
                    f"{message}\n"
                    f"Number of results: {len(data)}"
                )

            return message

        # ----------------------------------------------------
        # RAG result
        # ----------------------------------------------------

        if rag_context:

            first_result = rag_context[0]

            if isinstance(
                first_result,
                dict
            ):

                content = first_result.get(
                    "content"
                )

                if content:

                    return str(
                        content
                    )

            return str(
                first_result
            )

        # ----------------------------------------------------
        # Nothing available
        # ----------------------------------------------------

        return (
            "I couldn't find specific plan information "
            "for your request."
        )