import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent

    Responsibilities:
    1. Understand the user's request.
    2. Classify the request into the correct specialized agent.
    3. Use Gemini as the primary classifier.
    4. Fall back to rule-based classification if Gemini fails.
    """

    VALID_AGENTS = {
        "billing",
        "plans",
        "payment",
        "technical",
        "general",
    }

    def __init__(self, gemini=None):
        """
        gemini:
            Existing Gemini service/client from backend/app/gemini.py.

        We inject it instead of creating another Gemini client here.
        """
        self.gemini = gemini

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for the Supervisor Agent.

        Returns:
            {
                "agent": "billing",
                "confidence": 0.95,
                "reason": "...",
                "method": "gemini"
            }
        """

        if not query or not query.strip():
            return {
                "agent": "general",
                "confidence": 1.0,
                "reason": "Empty user query.",
                "method": "fallback",
            }

        query = query.strip()

        # ---------------------------------------------------------
        # 1. Try Gemini classification
        # ---------------------------------------------------------
        if self.gemini is not None:
            try:
                result = await self._classify_with_gemini(
                    query=query,
                    context=context,
                )

                if result and result["agent"] in self.VALID_AGENTS:
                    return result

            except Exception as exc:
                logger.warning(
                    "Gemini classification failed: %s",
                    exc,
                )

        # ---------------------------------------------------------
        # 2. Rule-based fallback
        # ---------------------------------------------------------
        return self._classify_with_rules(query)

    async def _classify_with_gemini(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Classify the query using the existing Gemini service.

        IMPORTANT:
        The exact Gemini method may need to be changed depending
        on your team's gemini.py implementation.
        """

        prompt = self._build_prompt(query, context)

        # ---------------------------------------------------------
        # Adapter section
        # ---------------------------------------------------------
        #
        # Your existing gemini.py may expose something like:
        #
        #   await self.gemini.generate(prompt)
        #
        # or:
        #
        #   await self.gemini.generate_response(prompt)
        #
        # or:
        #
        #   await self.gemini.chat(prompt)
        #
        # Change ONLY the following call when you see gemini.py.
        # ---------------------------------------------------------

        if hasattr(self.gemini, "generate"):
            response = await self.gemini.generate(prompt)

        elif hasattr(self.gemini, "generate_response"):
            response = await self.gemini.generate_response(prompt)

        elif hasattr(self.gemini, "chat"):
            response = await self.gemini.chat(prompt)

        else:
            raise AttributeError(
                "Gemini service does not have a supported "
                "generate/generate_response/chat method."
            )

        return self._parse_gemini_response(response)

    def _build_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Prompt for multilingual intent classification.
        """

        previous_context = ""

        if context:
            history = context.get("history")

            if history:
                previous_context = (
                    f"\nConversation history:\n{history}\n"
                )

        return f"""
You are the Supervisor Agent for a multilingual customer service
voice assistant.

Your job is ONLY to classify the user's request.

Available agents:

1. billing
   - bills
   - invoices
   - charges
   - billing amount
   - billing history
   - due dates
   - late fees

2. plans
   - available plans
   - plan pricing
   - plan comparison
   - plan upgrade
   - plan downgrade
   - data plans
   - subscription plans

3. payment
   - payment status
   - failed payment
   - successful payment
   - transaction problems
   - refunds
   - payment history

4. technical
   - internet problems
   - network problems
   - slow internet
   - no signal
   - 5G problems
   - connectivity
   - network outage
   - technical troubleshooting

5. general
   - greetings
   - thanks
   - goodbye
   - general questions
   - questions that do not belong to the above categories

IMPORTANT:
- Understand multilingual queries.
- Do NOT translate the user's query.
- Do NOT answer the user's question.
- Only classify the intent.
- Return ONLY valid JSON.
- The "agent" value must be exactly one of:
  billing, plans, payment, technical, general.

Return this format:

{{
    "agent": "billing",
    "confidence": 0.95,
    "reason": "The user is asking about a billing charge."
}}

{previous_context}

User query:
{query}
"""

    def _parse_gemini_response(
        self,
        response: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Convert Gemini's response into our standard format.
        """

        if response is None:
            return None

        # Handle common Gemini response formats.
        if isinstance(response, dict):
            data = response

        else:
            text = str(response).strip()

            # Remove markdown JSON fences if Gemini adds them.
            text = re.sub(
                r"^```json\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )

            text = re.sub(
                r"\s*```$",
                "",
                text,
            )

            try:
                data = json.loads(text)

            except json.JSONDecodeError:
                # Try extracting a JSON object from the response.
                match = re.search(
                    r"\{.*\}",
                    text,
                    flags=re.DOTALL,
                )

                if not match:
                    logger.warning(
                        "Could not parse Gemini classification: %s",
                        text,
                    )
                    return None

                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None

        agent = str(data.get("agent", "")).lower().strip()

        if agent not in self.VALID_AGENTS:
            return None

        try:
            confidence = float(
                data.get("confidence", 0.0)
            )
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        return {
            "agent": agent,
            "confidence": confidence,
            "reason": data.get(
                "reason",
                "Classified by Gemini.",
            ),
            "method": "gemini",
        }

    def _classify_with_rules(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Lightweight fallback classifier.

        This is NOT the primary classifier.
        Gemini is preferred because the application is multilingual.
        """

        text = query.lower()

        billing_keywords = [
            "bill",
            "billing",
            "invoice",
            "charge",
            "charged",
            "charges",
            "due date",
            "late fee",
            "billing history",
        ]

        payment_keywords = [
            "payment",
            "paid",
            "pay",
            "refund",
            "transaction",
            "failed payment",
            "payment failed",
            "payment status",
        ]

        plans_keywords = [
            "plan",
            "plans",
            "subscription",
            "upgrade",
            "downgrade",
            "data plan",
            "pricing",
            "package",
        ]

        technical_keywords = [
            "internet",
            "network",
            "signal",
            "5g",
            "4g",
            "wifi",
            "connectivity",
            "connection",
            "outage",
            "slow internet",
            "not working",
        ]

        # Payment before billing because phrases such as
        # "payment charge" can otherwise be classified as billing.
        if self._contains_keyword(text, payment_keywords):
            return {
                "agent": "payment",
                "confidence": 0.70,
                "reason": "Matched payment-related keywords.",
                "method": "rule_fallback",
            }

        if self._contains_keyword(text, billing_keywords):
            return {
                "agent": "billing",
                "confidence": 0.70,
                "reason": "Matched billing-related keywords.",
                "method": "rule_fallback",
            }

        if self._contains_keyword(text, plans_keywords):
            return {
                "agent": "plans",
                "confidence": 0.70,
                "reason": "Matched plan-related keywords.",
                "method": "rule_fallback",
            }

        if self._contains_keyword(text, technical_keywords):
            return {
                "agent": "technical",
                "confidence": 0.70,
                "reason": "Matched technical/network keywords.",
                "method": "rule_fallback",
            }

        return {
            "agent": "general",
            "confidence": 0.50,
            "reason": "No specialized intent was detected.",
            "method": "rule_fallback",
        }

    @staticmethod
    def _contains_keyword(
        text: str,
        keywords: list,
    ) -> bool:
        """
        Check whether any keyword appears in the query.
        """

        return any(
            keyword in text
            for keyword in keywords
        )