from typing import Any, Dict, Optional

from app.context import get_or_create_session
from app.gemini import generate_text
from app.rag import retrieve_context
from app.validation import (
    validate_customer_query,
    validate_language,
    validate_session_id,
)


class Orchestrator:
    """
    Coordinates the main processing flow of the
    multilingual GenAI voice assistant.
    """

    def __init__(self):
        pass

    async def process_text(
        self,
        session_id: str,
        customer_query: str,
        language: str = "en",
        customer_id: Optional[str] = None,
        nlu_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer text request.

        Flow:
            Customer Query
                ↓
            Validation
                ↓
            Session Context
                ↓
            RAG
                ↓
            Gemini
                ↓
            Response
        """

        # -------------------------
        # Validate input
        # -------------------------

        session_id = validate_session_id(session_id)
        customer_query = validate_customer_query(customer_query)
        language = validate_language(language)

        # -------------------------
        # Get or create session
        # -------------------------

        context = get_or_create_session(
            session_id=session_id,
            customer_id=customer_id,
            language=language,
        )

        # Store customer message
        context.add_message(
            role="customer",
            content=customer_query,
            language=language,
        )

        # -------------------------
        # Prepare NLU data
        # -------------------------

        if nlu_data is None:
            nlu_data = {
                "request_id": session_id,
                "language": {
                    "primary": language,
                    "code_switched": False,
                },
                "intent": {
                    "name": "general_query",
                },
                "entities": {},
                "sentiment": {
                    "label": "neutral",
                },
                "customer_query": customer_query,
            }

        # -------------------------
        # Retrieve RAG context
        # -------------------------

        rag_result = retrieve_context(nlu_data)

        # -------------------------
        # Build Gemini prompt
        # -------------------------

        prompt = self._build_prompt(
            customer_query=customer_query,
            language=language,
            rag_result=rag_result,
            context=context,
        )

        # -------------------------
        # Generate response
        # -------------------------

        response = await generate_text(prompt)

        # Store assistant response
        context.add_message(
            role="assistant",
            content=response,
            language=language,
        )

        return {
            "session_id": session_id,
            "language": language,
            "response": response,
            "rag": rag_result,
        }

    def _build_prompt(
        self,
        customer_query: str,
        language: str,
        rag_result: Any,
        context: Any,
    ) -> str:
        """
        Build the prompt sent to Gemini.
        """

        history = context.get_history()

        return f"""
You are a multilingual telecom customer-care assistant.

Respond in the customer's language.

Language:
{language}

Customer query:
{customer_query}

Retrieved telecom knowledge:
{rag_result}

Conversation history:
{history}

Rules:
- Answer only using the available information.
- Do not invent customer account or billing information.
- If the retrieved information is insufficient, say that
  the information needs to be checked.
- Keep the response concise and professional.
"""
    

# Shared orchestrator instance
orchestrator = Orchestrator()