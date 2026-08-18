from typing import Any, Dict

from backend.app.gemini import generate_text


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
                "response": "How can I help you today?",
                "success": True,
                "confidence": 1.0,
                "tool_used": None,
                "tool_result": None,
                "rag_context": None,
                "requires_customer_id": False,
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
            "response": response,
            "success": True,
            "confidence": 0.95,
            "tool_used": None,
            "tool_result": None,
            "rag_context": None,
            "requires_customer_id": False,
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

            return self._build_fallback_response(query)

    # ==========================================================
    # FALLBACK
    # ==========================================================

    @staticmethod
    def _build_fallback_response(query: str) -> str:
        text = query.lower().strip()

        if any(word in text for word in ("hi", "hello", "hey", "vanakkam", "namaste")):
            return "Hello. I can help with billing, payments, plans, network issues, and account support."

        if any(word in text for word in ("thank", "thanks")):
            return "You're welcome. Is there anything else I can help you with?"

        if any(word in text for word in ("bye", "goodbye", "exit")):
            return "Thank you for contacting support. Have a good day."

        if "help" in text or "what can you" in text:
            return (
                "I can help with current bills, payment status, plan details, "
                "network problems, and escalation to a human agent."
            )

        return (
            "I can help with telecom support. Please ask about billing, "
            "payments, plans, or network issues."
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
