from typing import Any, Dict


class GeneralAgent:
    """
    General-purpose customer service agent.

    This agent handles basic/general customer queries that do not
    require Network Tool, Plans Tool, Billing Tool, or Payment Tool.

    Examples:
        - Hello
        - Hi
        - What can you help me with?
        - How can I use this service?
        - What services do you provide?
        - Thank you
        - Bye
    """

    def __init__(self, rag: Any, tools: Any, gemini: Any):
        """
        Args:
            rag:
                RAG interface. Currently not required by the General Agent,
                but kept to maintain the common agent interface.

            tools:
                Tools registry/container. Currently not required by the
                General Agent.

            gemini:
                Gemini wrapper used to generate the final response.
        """

        self.rag = rag
        self.tools = tools
        self.gemini = gemini

    # ============================================================
    # MAIN HANDLER
    # ============================================================

    async def handle(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a general customer query.

        Args:
            query:
                User's current question.

            context:
                Conversation context containing information such as:

                {
                    "customer_id": "...",
                    "language": "English",
                    "conversation_id": "...",
                    "history": [...],
                    "current_agent": "general"
                }

        Returns:
            Structured response for the orchestrator.
        """

        language = context.get(
            "language",
            "English"
        )

        # --------------------------------------------------------
        # Generate response
        # --------------------------------------------------------

        response_text = await self._generate_response(
            query=query,
            language=language,
            context=context
        )

        # --------------------------------------------------------
        # Return standard agent response
        # --------------------------------------------------------

        return {
            "agent": "general",
            "used_rag": False,
            "used_tool": False,
            "rag_context": [],
            "tool_data": None,
            "response": response_text
        }

    # ============================================================
    # GENERATE RESPONSE
    # ============================================================

    async def _generate_response(
        self,
        query: str,
        language: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate the final response using Gemini.

        The General Agent does not call any business/database tool.
        """

        prompt = self._build_prompt(
            query=query,
            language=language,
            context=context
        )

        # --------------------------------------------------------
        # Gemini integration
        # --------------------------------------------------------

        try:

            # Expected Gemini interface:
            #
            # await self.gemini.generate(
            #     prompt=prompt,
            #     context=context,
            #     target_language=language
            # )

            response = await self.gemini.generate(
                prompt=prompt,
                context=context,
                target_language=language
            )

            return response

        except Exception as e:

            return (
                "I'm sorry, I couldn't process your request right now. "
                "Please try again."
            )

    # ============================================================
    # BUILD GEMINI PROMPT
    # ============================================================

    def _build_prompt(
        self,
        query: str,
        language: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build the prompt sent to Gemini.
        """

        history = context.get(
            "history",
            []
        )

        return f"""
You are the General Customer Support Agent for a telecom
customer service system.

Your responsibility is to answer simple and general customer
questions.

You MUST NOT invent:
- customer billing information
- payment information
- network status
- plan information
- account information
- technical issue information

If the user asks for specific information that requires
database/tool access, politely indicate that the appropriate
specialized service will handle it.

For general conversation:
- Be helpful.
- Be polite.
- Be concise.
- Do not provide unnecessary technical details.
- Maintain a professional customer-service tone.
- Respond in the requested language.

Requested language:
{language}

Conversation history:
{history}

User query:
{query}

Provide the best possible customer-service response.
"""