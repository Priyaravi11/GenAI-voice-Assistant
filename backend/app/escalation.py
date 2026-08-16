"""
Escalation Handler (Display-Only Version)
File: backend/app/escalation.py

What this does:
    1. Checks if the current agent result says escalation is needed
       (agent sets "escalate": True in the dict it returns from handle(),
       decided by the RAG -> Tool pipeline finding no answer).
    2. If yes, returns a message to DISPLAY/SPEAK to the user telling
       them their request couldn't be satisfied and they're being
       connected to a senior technical executive.
    3. No Twilio, no calls, no real connection — message-only response.

IMPORTANT — deliberately does NOT import gemini.py:
    Escalation is the fallback path for when things go wrong (no RAG
    match, no Tool match, or an upstream failure). If this file relied
    on calling Gemini to generate its message, a Gemini outage would
    break escalation at exactly the moment it's needed most. Messages
    are hardcoded per language instead — reliable and instant.

    gemini.py's SYSTEM_INSTRUCTION tells Gemini to MENTION escalation
    conversationally — that does not decide routing. The "escalate"
    flag set by each agent (from the RAG/Tool pipeline) is the single
    source of truth for whether escalation actually happens.

Languages: matches SUPPORTED_LANGUAGES in gemini.py exactly —
    English, Tamil, Hindi, Telugu, Kannada, Malayalam.
    Default: English (used if language is missing or unrecognized).
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EscalationManager:

    def should_escalate(self, agent_result: Dict[str, Any]) -> bool:
        """
        Simple check: did the agent itself decide to escalate?
        Every agent's handle() should set "escalate": True/False in
        its returned dict, based on the RAG -> Tool pipeline finding
        no answer (see answer_pipeline.py).
        """
        return bool(agent_result.get("escalate", False))

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