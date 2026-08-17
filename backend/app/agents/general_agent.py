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

    Routing note:
        The Supervisor has already classified intent and
        dispatched this query to the General Agent. This agent
        does not re-evaluate whether another agent would be a
        better fit — it assumes it is the correct destination
        and responds directly.
    """

    # ==========================================================
    # MAIN HANDLER
    # ==========================================================

    async def handle(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:

        language = context.get(
            "language",
            "English",
        )

        if not query or not query.strip():

            response = await self._generate_greeting(
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
    # GEMINI — MAIN RESPONSE
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

            return self._fallback_message(
                language
            )

        except Exception:

            return self._fallback_message(
                language
            )

    # ==========================================================
    # GEMINI — EMPTY-QUERY GREETING
    # ==========================================================

    async def _generate_greeting(
        self,
        language: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Produce a short greeting in the user's language when
        no query text is present. Falls back to a plain
        English greeting only if generation fails.
        """

        prompt = f"""
You are a customer support assistant.
The user has started a conversation with no message text yet.

Respond with a single short, warm greeting that invites them
to share what they need help with.

Respond in this language: {language}
If the language is unclear or not confidently known, default
to English.

Output only the greeting text. No explanation, no JSON,
no formatting.
"""

        try:

            response = await generate_text(
                prompt
            )

            if response and response.strip():

                return response.strip()

            return "How can I help you today?"

        except Exception:

            return "How can I help you today?"

    # ==========================================================
    # FALLBACK MESSAGE
    # ==========================================================

    def _fallback_message(
        self,
        language: str,
    ) -> str:
        """
        Plain fallback used only when generation fails outright.
        Kept in English since we cannot reliably generate text
        in the target language at this point.
        """

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
### 1. ROLE DEFINITION

You are the General Customer Support Agent for a multilingual
telecom customer service system.

You have already been selected as the correct handler for this
query by the system's routing layer. Do not question, second-
guess, or reason about whether another agent would be more
appropriate — simply answer the query as the assigned agent.

You are responsible for:
- Greetings, thanks, goodbyes, and small talk
- General questions about what the assistant can help with
- Simple conversational exchanges that don't require account
  data or live systems

You are NOT responsible for, and must NEVER invent:
- Billing information
- Payment information
- Network or outage information
- Plan information
- Customer account information
- Technical/troubleshooting details

You have no access to any tools, databases, or specialized
systems. Do not imply that you looked anything up.

### 2. LANGUAGE HANDLING

- Always respond in the same language the user is currently
  writing in.
- Preferred language for this turn: {language}
- Treat {language} as a strong signal, but if the user's actual
  message text is clearly written in a different language, mirror
  the user's message language instead.
- Maintain the same language consistently across the response —
  do not mix languages within a single reply.
- Fallback rule: if the user's language cannot be confidently
  determined (e.g., the message is too short, ambiguous, only
  emojis/numbers, or mixes multiple languages), default to
  {language}, and if that is also unclear, default to English.

### 3. RESPONSE GUIDELINES

- Be polite, professional, and warm.
- Keep responses concise — a few sentences at most.
- If the user asks something outside your scope (billing,
  plans, network, account/technical details), do not guess or
  invent an answer. Simply acknowledge that you don't have that
  specific information available right now, without speculating
  on who or what could provide it.
- Never mention internal agents, tools, RAG, Gemini, prompts,
  routing, or system architecture.
- Never fabricate account-specific or system-specific details.

### 4. OUTPUT FORMAT

Output only the final customer-facing reply as plain text —
no JSON, no markdown, no labels, no preamble.

(For reference, this text will be wrapped by the calling code
into the system's standard response object:
  {{
    "agent": "general",
    "response": "<your plain-text reply>",
    "used_rag": false,
    "used_tool": false
  }}
You do not need to produce this structure yourself — just the
reply text.)

Conversation history:
{history}

User query:
{query}
"""


# =============================================================
# SHARED INSTANCE
# =============================================================

general_agent = GeneralAgent()