import json
import logging
import re
from typing import Any, Dict, Optional

from app.gemini import generate_text


logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent

    Responsibilities:
    1. Understand the user's request.
    2. Classify the request into the correct specialized agent.
    3. Use Gemini as the primary classifier.
    4. Fall back to rule-based classification if Gemini fails or
       returns low confidence (below MIN_CONFIDENCE).

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

    # Gemini classifications below this confidence are treated as
    # unreliable and the request falls back to rule-based matching.
    MIN_CONFIDENCE = 0.3

    # Patterns that plausibly look like an "answer" to a pending
    # customer-specific request (e.g. a customer ID) rather than a
    # brand-new intent. Kept intentionally narrow and conservative:
    # short, no obvious sentence structure, no digits-only phone-like
    # spam. Adjust to match your actual customer ID format.
    _PENDING_ANSWER_PATTERN = re.compile(
        r"^[A-Za-z]{1,4}\d{2,10}$"
    )

    # Max token/word count for a message to be considered a plausible
    # "short answer" to a pending slot (customer ID, OTP, etc.) rather
    # than a new full-sentence request.
    _PENDING_ANSWER_MAX_WORDS = 3

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
        # Continue pending customer-specific request
        # -----------------------------------------------------
        # NOTE: this is deliberately gated, not an unconditional
        # bypass. If a tool is pending (e.g. billing asked for a
        # customer ID) but the user's new message doesn't actually
        # look like an answer to that pending slot -- e.g. they
        # changed topic entirely -- we must NOT force it back to
        # current_agent. Otherwise a mid-flow topic switch like
        # "actually, what plans do you have?" gets silently routed
        # back to billing and the user's real request is dropped.
        # -----------------------------------------------------

        required_tool = context.get("required_tool")
        current_agent = context.get("current_agent")

        if (
            required_tool
            and current_agent in self.VALID_AGENTS
            and self._looks_like_pending_answer(query)
        ):
            return {
                "agent": current_agent,
                "confidence": 1.0,
                "reason": "Continuing a pending multi-turn request.",
                "method": "context",
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

                if result.get("confidence", 1.0) < self.MIN_CONFIDENCE:

                    logger.warning(
                        "Gemini confidence too low (%.2f), "
                        "falling back to rule-based classification.",
                        result.get("confidence", 0.0),
                    )

                else:
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
    # PENDING-ANSWER HEURISTIC
    # ---------------------------------------------------------

    def _looks_like_pending_answer(self, query: str) -> bool:
        """
        Conservative heuristic for "does this message look like it's
        answering a pending slot (customer ID, OTP, etc.) rather than
        stating a brand-new request?"

        This intentionally errs on the side of NOT bypassing
        classification -- a false negative here just means the query
        goes through normal Gemini/rule classification (safe). A
        false positive would wrongly force the query back to
        current_agent even though it's a new topic (unsafe), so the
        checks below are kept narrow.
        """

        text = query.strip()

        if not text:
            return False

        word_count = len(text.split())

        if word_count > self._PENDING_ANSWER_MAX_WORDS:
            return False

        # If it matches a short alphanumeric/ID-like pattern, treat
        # it as a plausible pending-slot answer.
        if self._PENDING_ANSWER_PATTERN.match(text.replace(" ", "")):
            return True

        # Otherwise, only accept very short non-sentence-like replies
        # (e.g. "yes", "ok", a single word with no other agent's
        # keyword in it). Reject anything containing another agent's
        # obvious trigger words so an actual topic switch isn't
        # swallowed.
        other_topic_words = [
            "bill", "billing", "invoice", "charge",
            "plan", "plans", "package", "upgrade", "downgrade",
            "payment", "paid", "refund", "transaction",
            "internet", "network", "signal", "wifi",
        ]

        lowered = text.lower()

        if any(word in lowered for word in other_topic_words):
            return False

        return word_count <= 2

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
        language = context.get("language", "English")
        entities = context.get("entities", {})
        sentiment = context.get("sentiment", "neutral")
        code_switched = context.get("code_switched", False)

        # Serialize structured fields as JSON rather than relying on
        # Python repr via f-string interpolation, so Gemini reliably
        # sees valid JSON in the prompt rather than e.g. single-quoted
        # dict/list syntax.
        try:
            history_json = json.dumps(history, ensure_ascii=False)
        except (TypeError, ValueError):
            history_json = "[]"

        try:
            entities_json = json.dumps(entities, ensure_ascii=False)
        except (TypeError, ValueError):
            entities_json = "{}"

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

Customer language:
{language}

Entities:
{entities_json}

Sentiment:
{sentiment}

Code-switched:
{code_switched}

Conversation history:
{history_json}

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
                # Second attempt: extract the first structurally
                # valid JSON object from the text.
                #
                # NOTE: a naive greedy regex like r"\{.*\}" would
                # span from the FIRST "{" to the LAST "}" in the
                # whole response. If Gemini echoes an example or
                # adds trailing notes containing their own braces,
                # that regex over-matches and produces invalid
                # JSON even when a valid object was extractable.
                # json.JSONDecoder().raw_decode avoids this by
                # parsing from a starting "{" and stopping as soon
                # as it finds one complete, valid object.
                # ---------------------------------------------

                start = text.find("{")

                if start == -1:

                    logger.warning(
                        "Unable to parse Gemini response: %s",
                        text,
                    )

                    return None

                decoder = json.JSONDecoder()

                try:

                    data, _ = decoder.raw_decode(text, start)

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

        text = query.lower().strip()

        # ==========================================================
        # COMBINED / AMBIGUOUS CASES
        # ==========================================================
        # Checked before the individual categories below. Example:
        # "I made a payment but my bill still shows unpaid" contains
        # both "payment" and "bill", and the underlying issue is the
        # bill/invoice state, not the payment itself.
        # ==========================================================

        if self._contains_keyword(
            text,
            ["payment"],
        ) and self._contains_keyword(
            text,
            ["bill", "billing", "invoice"],
        ):
            return {
                "agent": "billing",
                "confidence": 0.80,
                "reason": (
                    "The main issue concerns a bill that has not "
                    "been updated after payment."
                ),
                "method": "rule_fallback",
            }

        # ==========================================================
        # PAYMENT
        # ==========================================================
        # NOTE: intentionally do NOT add a generic "pay" keyword here.
        # "pay" is a substring of many unrelated phrases (e.g. "pay for
        # my bill", "payslip") and, unlike "payment"/"paid", it is too
        # short and too common to be a reliable signal even with
        # word-boundary matching. Keep this list to "payment" and
        # "paid" only.
        # ==========================================================

        payment_keywords = [
            "payment failed",
            "failed payment",
            "payment status",
            "payment history",
            "latest payment",
            "last payment",
            "payment issue",
            "payment problem",
            "refund",
            "transaction",
            "payment",
            "paid",
        ]

        # ==========================================================
        # BILLING
        # ==========================================================

        billing_keywords = [
            "current bill",
            "previous bill",
            "last bill",
            "bill history",
            "billing history",
            "billing",
            "invoice",
            "bill amount",
            "bill",
            "charge",
            "charged",
            "charges",
            "due date",
            "late fee",
            "duplicate bill",
            "double bill",
        ]

        # ==========================================================
        # PLANS
        # ==========================================================

        plans_keywords = [
            "available plan",
            "available plans",
            "plan pricing",
            "plan comparison",
            "compare plans",
            "upgrade plan",
            "downgrade plan",
            "data plan",
            "subscription",
            "plans",
            "plan",
            "package",
        ]

        # ==========================================================
        # TECHNICAL
        # ==========================================================

        technical_keywords = [
            "internet not working",
            "internet problem",
            "network problem",
            "network issue",
            "no signal",
            "weak signal",
            "slow internet",
            "mobile data not working",
            "4g problem",
            "5g problem",
            "4g not working",
            "5g not working",
            "network outage",
            "connectivity problem",
            "connection problem",
            "internet",
            "network",
            "signal",
            "wifi",
        ]

        # ==========================================================
        # ORDER
        # ==========================================================
        # Check the most specific categories first.
        # ==========================================================

        if self._contains_keyword(
            text,
            payment_keywords,
        ):
            return {
                "agent": "payment",
                "confidence": 0.70,
                "reason": (
                    "Matched payment-related keywords."
                ),
                "method": "rule_fallback",
            }

        if self._contains_keyword(
            text,
            billing_keywords,
        ):
            return {
                "agent": "billing",
                "confidence": 0.70,
                "reason": (
                    "Matched billing-related keywords."
                ),
                "method": "rule_fallback",
            }

        if self._contains_keyword(
            text,
            plans_keywords,
        ):
            return {
                "agent": "plans",
                "confidence": 0.70,
                "reason": (
                    "Matched plan-related keywords."
                ),
                "method": "rule_fallback",
            }

        if self._contains_keyword(
            text,
            technical_keywords,
        ):
            return {
                "agent": "technical",
                "confidence": 0.70,
                "reason": (
                    "Matched technical/network keywords."
                ),
                "method": "rule_fallback",
            }

        # ==========================================================
        # GENERAL
        # ==========================================================

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
        Check whether a keyword appears in the query as a whole
        word/phrase, using Unicode-aware word boundaries.

        This avoids false positives such as "plan" matching inside
        "implantation" or "airplane".
        """

        for keyword in keywords:

            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

            if re.search(pattern, text):
                return True

        return False


# =============================================================
# SHARED SUPERVISOR INSTANCE
# =============================================================

supervisor_agent = SupervisorAgent()