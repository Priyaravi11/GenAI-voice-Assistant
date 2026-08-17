from typing import Any, Dict, Optional

from app.gemini import generate_text

# ============================================================
# PLAN TOOLS
# ============================================================

from backend.tools.plans_tool import (
    get_current_plan,
    get_plan_details,
    get_available_plans,
    compare_plans,
    find_plans,
    get_plan_change_info,
)


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
                RAG system for general plan-related knowledge.

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

        customer_id: Optional[str] = context.get(
            "customer_id"
        )

        language: str = context.get(
            "language",
            "English"
        )

        # ----------------------------------------------------
        # Detect required plan tool
        # ----------------------------------------------------

        tool_name = self._select_plan_tool(query)

        # ----------------------------------------------------
        # Check whether general plan knowledge is needed
        # ----------------------------------------------------

        needs_rag = self._requires_general_plan_knowledge(
            query
        )

        rag_context = []
        tool_data = None

        # ====================================================
        # STEP 1: RAG
        # ====================================================

        if needs_rag:
            rag_context = await self._query_plan_rag(
                query
            )

        # ====================================================
        # STEP 2: PLAN TOOL
        # ====================================================

        if tool_name:

            tool_data = await self._execute_plan_tool(
                tool_name=tool_name,
                query=query,
                customer_id=customer_id,
                context=context,
            )

        # ====================================================
        # STEP 3: GEMINI
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
            "agent": "plans",
            "used_rag": bool(rag_context),
            "used_tool": tool_data is not None,
            "tool_name": tool_name,
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
    # EXECUTE PLAN TOOL
    # ========================================================

    async def _execute_plan_tool(
        self,
        tool_name: str,
        query: str,
        customer_id: Optional[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the actual Plans Tool function.

        IMPORTANT:
        These are the real functions from plans_tool.py.
        """

        try:

            # =================================================
            # CURRENT PLAN
            # =================================================

            if tool_name == "get_current_plan":

                if not customer_id:

                    return {
                        "success": False,
                        "requires_customer_id": True,
                        "message": (
                            "Sure, I can check your current plan. "
                            "Could you please provide your customer ID?"
                        )
                    }

                return get_current_plan(
                    customer_id
                )

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
            # AVAILABLE PLANS
            # =================================================

            if tool_name == "get_available_plans":

                return get_available_plans()

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
                        "message": (
                            "Sure, I can help with changing your plan. "
                            "Could you please provide your customer ID?"
                        )
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
    # RAG
    # ========================================================

    async def _query_plan_rag(
        self,
        query: str
    ) -> list:
        """
        Query the plan-related RAG system.
        """

        if self.rag is None:
            return []

        try:

            if hasattr(
                self.rag,
                "query"
            ):

                result = self.rag.query(
                    query,
                    category="plans"
                )

                if hasattr(
                    result,
                    "__await__"
                ):

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
        tool_data: Optional[
            Dict[str, Any]
        ],
        context: Dict[str, Any],
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
    ) -> str:
        """
        Build Gemini prompt.
        """

        return f"""
You are a telecom plans assistant.

Answer the customer's question clearly and accurately.

Customer language:
{language}

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
5. Respond in the customer's requested language.
6. Keep the answer concise and helpful.
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