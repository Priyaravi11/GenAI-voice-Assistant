"""
Escalation Handler (Display-Only Version)
File: backend/app/escalation.py

UPDATED to match the REAL agent implementations (billing_agent.py,
general_agent.py, payment_agent.py, plans_agent.py, technical_agent.py,
supervisor_agent.py) — none of them set an "escalate" key directly.
should_escalate() now reads the actual signals each agent produces.

Per-agent escalation signal:
    billing / payment  -> "success": False
                           (only set on exception or invalid/empty query;
                           there is currently no explicit "nothing found"
                           signal beyond that in these two agents)
    plans / technical  -> used_rag=False AND used_tool=False together
                           (agent found nothing via either path)
                        -> OR tool_data present but tool_data["success"]
                           is False (the tool ran but failed/found nothing)
    general             -> NEVER escalates via this logic. It always has
                           used_rag=False, used_tool=False by design (it
                           doesn't use either) — that is normal, not a
                           failure. Excluding it explicitly prevents every
                           greeting/thanks message from wrongly escalating.
    supervisor          -> not applicable. Its output is a ROUTING decision
                           (which agent to use), not a final answer —
                           should_escalate() should not be called on it.

NOTE: tool_data's exact shape (what "success": False looks like from a
REAL tool call) is confirmed here based on the agents' own code, which
already checks tool_data.get("success"). Once the actual tools/*.py
files are shared, this logic may need a small adjustment if their
real output shape differs from what the agents currently expect —
flagged as the one open question until tools code arrives.

No Twilio, no calls, no real connection — this is a message-only
response for the orchestrator to show/speak back to the user.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Agents where "found nothing via RAG or Tool" is a valid escalation signal.
# General is deliberately excluded — see module docstring.
_RAG_TOOL_AGENTS = {"plans", "technical"}

# Agents that report success/failure directly instead of used_rag/used_tool.
_SUCCESS_FLAG_AGENTS = {"billing", "payment"}


class EscalationManager:

    def should_escalate(self, agent_result: Dict[str, Any]) -> bool:
        """
        Reads the REAL signals each agent produces (see module docstring)
        rather than a uniform "escalate" flag, since none of the agents
        currently set one.

        Still checks "escalate" first for forward-compatibility, in case
        an agent is updated later to set it directly — but no current
        agent does.
        """
        if "escalate" in agent_result:
            return bool(agent_result["escalate"])

        agent_name = agent_result.get("agent")

        # --- billing / payment: explicit success flag ---
        if agent_name in _SUCCESS_FLAG_AGENTS:
            return agent_result.get("success", True) is False

        # --- plans / technical: RAG/Tool signals ---
        if agent_name in _RAG_TOOL_AGENTS:
            used_rag = bool(agent_result.get("used_rag"))
            used_tool = bool(agent_result.get("used_tool"))

            if not used_rag and not used_tool:
                return True

            tool_data = agent_result.get("tool_data")
            if isinstance(tool_data, dict) and tool_data.get("success") is False:
                return True

            return False

        # --- general: never escalates via this check (see docstring) ---
        # --- supervisor / unknown agent: not applicable, don't escalate ---
        return False

    def handle_escalation(self, reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call this when should_escalate() returns True.

        Returns a dict the orchestrator can display/speak back to the
        user as the final response for this turn. No external calls
        are made — this is purely a message to show on screen.
        """
        language = context.get("language", "English")
        message = self._get_message(language)

        logger.info("Escalation triggered. reason=%s language=%s", reason, language)

        return {
            "agent": "escalation",
            "escalated": True,
            "reason": reason,
            "response": message,
            "language": language,
        }

    def _get_message(self, language: str) -> str:
        if language == "Tamil":
            return (
                "மன்னிக்கவும், உங்கள் கோரிக்கையை என்னால் பூர்த்தி செய்ய முடியவில்லை. "
                "நான் உங்களை ஒரு மூத்த தொழில்நுட்ப நிர்வாகியிடம் இணைக்கிறேன்."
            )
        elif language == "Hindi":
            return (
                "क्षमा करें, मैं आपके अनुरोध को पूरा नहीं कर सकता। "
                "मैं आपको एक वरिष्ठ तकनीकी अधिकारी से जोड़ रहा हूं।"
            )
        elif language == "Telugu":
            return (
                "క్షమించండి, మీ అభ్యర్థనను నేను నెరవేర్చలేకపోతున్నాను. "
                "నేను మిమ్మల్ని సీనియర్ టెక్నికల్ ఎగ్జిక్యూటివ్‌తో కలుపుతున్నాను."
            )
        elif language == "Kannada":
            return (
                "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ನನಗೆ ಪೂರೈಸಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ. "
                "ನಾನು ನಿಮ್ಮನ್ನು ಹಿರಿಯ ತಾಂತ್ರಿಕ ಅಧಿಕಾರಿಯೊಂದಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತಿದ್ದೇನೆ."
            )
        elif language == "Malayalam":
            return (
                "ക്ഷമിക്കണം, നിങ്ങളുടെ അഭ്യർത്ഥന എനിക്ക് നിറവേറ്റാൻ കഴിയുന്നില്ല. "
                "ഞാൻ നിങ്ങളെ ഒരു സീനിയർ ടെക്നിക്കൽ എക്സിക്യൂട്ടീവുമായി ബന്ധിപ്പിക്കുന്നു."
            )
        else:
            # Default: English (also used for any unrecognized language value)
            return (
                "Sorry, we cannot satisfy your request. "
                "We will be connecting you to a senior technical executive."
            )