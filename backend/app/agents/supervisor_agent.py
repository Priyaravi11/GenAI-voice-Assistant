import json
import logging
import re
from typing import Any, Dict, Optional

from backend.app.gemini import generate_text


logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent

    Responsibilities:
    1. Understand the user's request.
    2. Classify the request into the correct specialized agent.
    3. Use Gemini as the primary classifier.
    4. Fall back to rule-based classification if Gemini fails.

    Available agents:
        - billing
        - plans
        - payment
        - technical
        - general
    """

    VALID_AGENTS = {
        "billing",
        "plans",
        "payment",
        "technical",
        "general",
    }

    # ---------------------------------------------------------
    # MAIN ENTRY POINT
    # ---------------------------------------------------------

    async def handle(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Classify the user's query and return the target agent.

        Example:

            result = await supervisor.handle(
                "Why is my bill so high?"
            )

        Returns:

            {
                "agent": "billing",
                "confidence": 0.95,
                "reason": "...",
                "method": "gemini"
            }
        """

        context = context or {}

        # -----------------------------------------------------
        # Validate query
        # -----------------------------------------------------

        if not isinstance(query, str):
            return {
                "agent": "general",
                "confidence": 0.0,
                "reason": "Invalid query type.",
                "method": "fallback",
            }

        query = query.strip()

        if not query:
            return {
                "agent": "general",
                "confidence": 1.0,
                "reason": "Empty user query.",
                "method": "fallback",
            }

        # -----------------------------------------------------
        # Primary classification: Gemini
        # -----------------------------------------------------

        try:

            result = await self._classify_with_gemini(
                query=query,
                context=context,
            )

            if result and result["agent"] in self.VALID_AGENTS:
                return result

        except Exception as exc:

            logger.warning(
                "Gemini supervisor classification failed: %s",
                exc,
            )

        # -----------------------------------------------------
        # Fallback classification: rules
        # -----------------------------------------------------

        logger.info(
            "Using rule-based supervisor fallback."
        )

        return self._classify_with_rules(query)

    # ---------------------------------------------------------
    # GEMINI CLASSIFICATION
    # ---------------------------------------------------------

    async def _classify_with_gemini(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Use the existing Gemini text-generation service
        to classify the user's intent.
        """

        prompt = self._build_classification_prompt(
            query=query,
            context=context,
        )

        # Your actual gemini.py exposes:
        #
        #     async def generate_text(prompt: str)
        #
        response = await generate_text(prompt)

        return self._parse_gemini_response(response)

    # ---------------------------------------------------------
    # GEMINI PROMPT
    # ---------------------------------------------------------

    def _build_classification_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build the Supervisor classification prompt.
        """

        context = context or {}

        history = context.get("history", [])

        return f"""
You are the Supervisor Agent of a multilingual telecom
customer-care voice assistant.

Your ONLY task is to classify the user's request.

Do NOT answer the user's question.

Choose exactly ONE of these agents:

1. billing
   Use for:
   - bills
   - invoices
   - billing amount
   - billing history
   - charges
   - due dates
   - late fees
   - unexpected bill charges

2. plans
   Use for:
   - available plans
   - plan pricing
   - plan comparison
   - plan upgrade
   - plan downgrade
   - subscription plans
   - data plans
   - packages

3. payment
   Use for:
   - payment status
   - failed payments
   - successful payments
   - transactions
   - payment history
   - refunds
   - refund status

4. technical
   Use for:
   - internet problems
   - network problems
   - slow internet
   - no signal
   - 4G/5G problems
   - connectivity problems
   - network outages
   - technical troubleshooting

5. general
   Use for:
   - greetings
   - thanks
   - goodbye
   - general questions
   - anything that does not belong to the
     specialized categories

IMPORTANT RULES:

- Understand English, Tamil, Hindi, Telugu, Kannada,
  Malayalam and code-switched queries.
- Do not translate the user's query.
- Do not answer the user's question.
- Return ONLY valid JSON.
- The agent value MUST be exactly:
  billing, plans, payment, technical, or general.
- Confidence must be a number between 0.0 and 1.0.

Return exactly this structure:

{{
    "agent": "billing",
    "confidence": 0.95,
    "reason": "The user is asking about a billing issue."
}}

Conversation history:
{history}

Current user query:
{query}
"""

    # ---------------------------------------------------------
    # PARSE GEMINI RESPONSE
    # ---------------------------------------------------------

    def _parse_gemini_response(
        self,
        response: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Parse Gemini's JSON classification response.
        """

        if response is None:
            return None

        # -----------------------------------------------------
        # If Gemini/helper already returns a dictionary
        # -----------------------------------------------------

        if isinstance(response, dict):

            data = response

        else:

            text = str(response).strip()

            if not text:
                return None

            # -------------------------------------------------
            # Remove markdown JSON code fences
            # -------------------------------------------------

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

            # -------------------------------------------------
            # First attempt: complete JSON response
            # -------------------------------------------------

            try:

                data = json.loads(text)

            except json.JSONDecodeError:

                # ---------------------------------------------
                # Second attempt: extract JSON object
                # ---------------------------------------------

                match = re.search(
                    r"\{.*\}",
                    text,
                    flags=re.DOTALL,
                )

                if not match:

                    logger.warning(
                        "Unable to parse Gemini response: %s",
                        text,
                    )

                    return None

                try:

                    data = json.loads(
                        match.group(0)
                    )

                except json.JSONDecodeError:

                    logger.warning(
                        "Invalid JSON returned by Gemini."
                    )

                    return None

        # -----------------------------------------------------
        # Validate agent
        # -----------------------------------------------------

        agent = str(
            data.get("agent", "")
        ).lower().strip()

        if agent not in self.VALID_AGENTS:

            logger.warning(
                "Gemini returned invalid agent: %s",
                agent,
            )

            return None

        # -----------------------------------------------------
        # Validate confidence
        # -----------------------------------------------------

        try:

            confidence = float(
                data.get(
                    "confidence",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # -----------------------------------------------------
        # Reason
        # -----------------------------------------------------

        reason = str(
            data.get(
                "reason",
                "Classified by Gemini.",
            )
        )

        return {
            "agent": agent,
            "confidence": confidence,
            "reason": reason,
            "method": "gemini",
        }

    # ---------------------------------------------------------
    # RULE-BASED FALLBACK
    # ---------------------------------------------------------

    def _classify_with_rules(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Lightweight fallback classifier.

        Gemini is the primary classifier.
        Rules are used only when Gemini fails.
        """

        text = query.lower()

        # -----------------------------------------------------
        # Payment
        # -----------------------------------------------------

        payment_keywords = [
            "payment",
            "paid",
            "pay",
            "refund",
            "transaction",
            "payment failed",
            "failed payment",
            "payment status",
        ]

        # -----------------------------------------------------
        # Billing
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Plans
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Technical
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Check payment first
        # -----------------------------------------------------

        if self._contains_keyword(
            text,
            payment_keywords,
        ):

            return {
                "agent": "payment",
                "confidence": 0.70,
                "reason": (
                    "Matched payment-related "
                    "keywords."
                ),
                "method": "rule_fallback",
            }

        # -----------------------------------------------------
        # Billing
        # -----------------------------------------------------

        if self._contains_keyword(
            text,
            billing_keywords,
        ):

            return {
                "agent": "billing",
                "confidence": 0.70,
                "reason": (
                    "Matched billing-related "
                    "keywords."
                ),
                "method": "rule_fallback",
            }

        # -----------------------------------------------------
        # Plans
        # -----------------------------------------------------

        if self._contains_keyword(
            text,
            plans_keywords,
        ):

            return {
                "agent": "plans",
                "confidence": 0.70,
                "reason": (
                    "Matched plan-related "
                    "keywords."
                ),
                "method": "rule_fallback",
            }

        # -----------------------------------------------------
        # Technical
        # -----------------------------------------------------

        if self._contains_keyword(
            text,
            technical_keywords,
        ):

            return {
                "agent": "technical",
                "confidence": 0.70,
                "reason": (
                    "Matched technical/network "
                    "keywords."
                ),
                "method": "rule_fallback",
            }

        # -----------------------------------------------------
        # Default
        # -----------------------------------------------------

        return {
            "agent": "general",
            "confidence": 0.50,
            "reason": (
                "No specialized intent was detected."
            ),
            "method": "rule_fallback",
        }

    # ---------------------------------------------------------
    # KEYWORD HELPER
    # ---------------------------------------------------------

    @staticmethod
    def _contains_keyword(
        text: str,
        keywords: list,
    ) -> bool:
        """
        Check whether a keyword appears in the query.
        """

        return any(
            keyword in text
            for keyword in keywords
        )


# =============================================================
# SHARED SUPERVISOR INSTANCE
# =============================================================

supervisor_agent = SupervisorAgent()