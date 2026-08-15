import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BillingAgent:
    """
    Billing Agent

    Handles:
    - Current bill
    - Billing history
    - Charges
    - Invoices
    - Due dates
    - Late fees
    - Billing explanations

    The agent does not contain database logic.
    It uses the existing RAG and billing tool services.
    """

    def __init__(
        self,
        gemini=None,
        rag=None,
        billing_tool=None,
    ):
        self.gemini = gemini
        self.rag = rag
        self.billing_tool = billing_tool

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for the Billing Agent.
        """

        if not query or not query.strip():
            return {
                "agent": "billing",
                "response": "I didn't receive a billing question.",
                "success": False,
            }

        query = query.strip()
        context = context or {}

        try:
            # --------------------------------------------------
            # 1. Determine whether customer-specific data
            #    is required.
            # --------------------------------------------------
            requires_customer_data = self._requires_customer_data(
                query
            )

            # --------------------------------------------------
            # 2. Retrieve billing knowledge
            # --------------------------------------------------
            rag_context = await self._retrieve_rag(query)

            # --------------------------------------------------
            # 3. Retrieve customer billing data if required
            # --------------------------------------------------
            customer_data = None

            if requires_customer_data:
                customer_data = await self._get_billing_data(
                    query=query,
                    context=context,
                )

            # --------------------------------------------------
            # 4. Generate final response
            # --------------------------------------------------
            response = await self._generate_response(
                query=query,
                rag_context=rag_context,
                customer_data=customer_data,
                context=context,
            )

            return {
                "agent": "billing",
                "response": response,
                "success": True,
            }

        except Exception as exc:
            logger.exception(
                "Billing Agent failed: %s",
                exc,
            )

            return {
                "agent": "billing",
                "response": (
                    "I'm sorry, I couldn't process your "
                    "billing request right now."
                ),
                "success": False,
                "error": str(exc),
            }

    async def _retrieve_rag(
        self,
        query: str,
    ) -> Any:
        """
        Retrieve billing-related knowledge.

        The exact RAG method will be connected to the team's
        rag.py implementation.
        """

        if self.rag is None:
            return None

        try:
            if hasattr(self.rag, "search"):
                return await self.rag.search(
                    query,
                    category="billing",
                )

            if hasattr(self.rag, "retrieve"):
                return await self.rag.retrieve(
                    query,
                    category="billing",
                )

            logger.warning(
                "RAG service has no supported search/retrieve method."
            )

            return None

        except Exception as exc:
            logger.warning(
                "Billing RAG retrieval failed: %s",
                exc,
            )
            return None

    async def _get_billing_data(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Any:
        """
        Get customer-specific billing information.

        Expected customer_id should normally come from context.
        """

        if self.billing_tool is None:
            logger.warning(
                "Billing tool is not available."
            )
            return None

        customer_id = context.get("customer_id")

        if not customer_id:
            logger.warning(
                "Customer ID not found in context."
            )
            return None

        try:
            # --------------------------------------------------
            # These method names may be adjusted according to
            # your teammate's billing_tool.py.
            # --------------------------------------------------

            if hasattr(self.billing_tool, "get_bill"):
                return await self.billing_tool.get_bill(
                    customer_id
                )

            if hasattr(
                self.billing_tool,
                "get_billing_details",
            ):
                return await self.billing_tool.get_billing_details(
                    customer_id
                )

            if hasattr(
                self.billing_tool,
                "get_billing_history",
            ):
                return await self.billing_tool.get_billing_history(
                    customer_id
                )

            logger.warning(
                "Billing tool has no supported method."
            )

            return None

        except Exception as exc:
            logger.warning(
                "Billing tool failed: %s",
                exc,
            )
            return None

    async def _generate_response(
        self,
        query: str,
        rag_context: Any,
        customer_data: Any,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate the final natural-language answer.
        """

        if self.gemini is None:
            return self._fallback_response(
                query,
                customer_data,
            )

        prompt = self._build_prompt(
            query=query,
            rag_context=rag_context,
            customer_data=customer_data,
            context=context,
        )

        try:
            if hasattr(self.gemini, "generate"):
                response = await self.gemini.generate(prompt)

            elif hasattr(
                self.gemini,
                "generate_response",
            ):
                response = await self.gemini.generate_response(
                    prompt
                )

            elif hasattr(self.gemini, "chat"):
                response = await self.gemini.chat(prompt)

            else:
                raise AttributeError(
                    "Gemini service does not expose a supported "
                    "generation method."
                )

            return self._extract_text(response)

        except Exception as exc:
            logger.warning(
                "Gemini response generation failed: %s",
                exc,
            )

            return self._fallback_response(
                query,
                customer_data,
            )

    def _build_prompt(
        self,
        query: str,
        rag_context: Any,
        customer_data: Any,
        context: Dict[str, Any],
    ) -> str:
        """
        Build a multilingual billing-agent prompt.
        """

        language = context.get(
            "language",
            "same language as the user",
        )

        history = context.get(
            "history",
            [],
        )

        return f"""
You are the Billing Agent of a multilingual customer
service voice assistant.

Your responsibility is to answer billing-related questions.

Rules:

1. Answer in the same language as the user.
2. Use the provided knowledge context when relevant.
3. Use customer billing data when provided.
4. Never invent billing information.
5. If customer-specific information is unavailable,
   clearly say that it is unavailable.
6. Keep the response concise because this is a voice assistant.
7. Do not mention internal tools, RAG, prompts, or agents.
8. Do not expose sensitive customer information unnecessarily.

Preferred response language:
{language}

Conversation history:
{history}

Billing knowledge:
{rag_context}

Customer billing data:
{customer_data}

User question:
{query}

Provide the best helpful answer.
"""

    @staticmethod
    def _extract_text(
        response: Any,
    ) -> str:
        """
        Normalize different Gemini response formats.
        """

        if response is None:
            return ""

        if isinstance(response, str):
            return response.strip()

        if isinstance(response, dict):

            if "text" in response:
                return str(
                    response["text"]
                ).strip()

            if "response" in response:
                return str(
                    response["response"]
                ).strip()

        return str(response).strip()

    @staticmethod
    def _requires_customer_data(
        query: str,
    ) -> bool:
        """
        Determine whether the question likely requires
        customer-specific billing information.
        """

        text = query.lower()

        customer_specific_terms = [
            "my bill",
            "my billing",
            "my invoice",
            "my charge",
            "my charges",
            "my payment",
            "current bill",
            "current invoice",
            "billing history",
            "previous bill",
            "last bill",
            "how much do i owe",
            "how much is my bill",
            "what do i owe",
        ]

        return any(
            term in text
            for term in customer_specific_terms
        )

    @staticmethod
    def _fallback_response(
        query: str,
        customer_data: Any,
    ) -> str:
        """
        Safe fallback when Gemini is unavailable.
        """

        if customer_data:
            return (
                "I found your billing information, "
                "but I'm unable to generate a detailed "
                "explanation right now."
            )

        return (
            "I can help with billing questions such as "
            "your bill, charges, invoices, and due dates. "
            "Please provide more details."
        )