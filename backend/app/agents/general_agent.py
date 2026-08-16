from typing import Any, Dict

from app.gemini import generate_text


class GeneralAgent:
    """
    General-purpose customer service agent.

    Handles:
        - Greetings
        - Thanks
        - Goodbye
        - General service questions
        - Basic conversation

    It does not access:
        - Billing tools
        - Payment tools
        - Plans tools
        - Network tools
        - Customer database
    """

    # ==========================================================
    # MAIN HANDLER
    # ==========================================================

    async def handle(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not query or not query.strip():

            return {
                "agent": "general",
                "used_rag": False,
                "used_tool": False,
                "response": (
                    "How can I help you today?"
                ),
            }

        language = context.get(
            "language",
            "English",
        )

        response = await self._generate_response(
            query=query,
            language=language,
            context=context,
        )

        return {
            "agent": "general",
            "used_rag": False,
            "used_tool": False,
            "rag_context": [],
            "tool_data": None,
            "response": response,
        }

    # ==========================================================
    # GEMINI
    # ==========================================================

    async def _generate_response(
        self,
        query: str,
        language: str,
        context: Dict[str, Any],
    ) -> str:

        prompt = self._build_prompt(
            query=query,
            language=language,
            context=context,
        )

        try:

            response = await generate_text(
                prompt
            )

            if response and response.strip():

                return response.strip()

            return (
                "I'm sorry, I couldn't process "
                "your request right now."
            )

        except Exception:

            return (
                "I'm sorry, I couldn't process "
                "your request right now. "
                "Please try again."
            )

    # ==========================================================
    # PROMPT
    # ==========================================================

    def _build_prompt(
        self,
        query: str,
        language: str,
        context: Dict[str, Any],
    ) -> str:

        history = context.get(
            "history",
            [],
        )

        return f"""
You are the General Customer Support Agent
for a multilingual telecom customer service system.

Your responsibility is to handle simple and
general customer conversations.

You can handle:
- Greetings
- Thanks
- Goodbye
- General questions
- Questions about what the assistant can help with

Do NOT invent:
- Billing information
- Payment information
- Network information
- Plan information
- Customer account information
- Technical information

If the user asks for information that requires
a specialized agent or database/tool access,
do not invent an answer.

Instead, politely explain that the appropriate
service needs to handle the request.

Rules:
1. Respond in the same language as the user.
2. Be polite and professional.
3. Keep the response concise.
4. Do not mention internal agents, tools, RAG,
   Gemini, prompts, or system architecture.
5. Do not provide unsupported information.

Language:
{language}

Conversation history:
{history}

User query:
{query}

Provide only the final customer-facing response.
"""


# =============================================================
# SHARED INSTANCE
# =============================================================

general_agent = GeneralAgent()