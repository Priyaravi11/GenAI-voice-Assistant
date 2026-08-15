import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(_name_)


class GeneralAgent:
    """
    General-purpose fallback agent for greetings, small talk, identity
    questions, thanks/goodbye, help/capability requests, complaint
    escalation, and unsupported queries.

    Follows the same interface as BillingAgent / PlansAgent / etc.
    so the orchestrator can call it uniformly:

        result = await general_agent.handle(query, context)
    """

    # ------------------------------------------------------------------
    # Intent patterns (mock heuristic layer).
    # Kept language-tolerant and includes common transliterated / code-
    # mixed forms since users type/speak Tamil & Hindi in Latin script
    # too (e.g. "vanakkam", "namaste", "kya haal hai"). Extend freely —
    # this is meant to be a living list, not exhaustive on day 1.
    # Replace/augment with Supervisor's real multilingual NLU once
    # available; this exists purely to avoid a Gemini round-trip for
    # cheap, high-confidence intents (latency priority).
    # ------------------------------------------------------------------

    GREETING_PATTERNS = [
        r"\bhi+\b", r"\bhello+\b", r"\bhey+\b", r"\byo\b",
        r"good\s?morning", r"good\s?afternoon", r"good\s?evening", r"good\s?night",
        # Tamil (script + transliteration)
        r"வணக்கம்", r"\bvanakkam\b",
        # Hindi (script + transliteration)
        r"नमस्ते", r"नमस्कार", r"\bnamaste\b", r"\bnamaskar\b",
        # Telugu (script + transliteration) — MVP is EN/TA/HI but keep
        # the door open per project's "later" language roadmap
        r"నమస్కారం", r"\bనమస్కారం\b", r"\bnamaskaram\b",
    ]

    IDENTITY_PATTERNS = [
        r"who are you", r"what are you", r"what can you do",
        r"how can you help", r"what do you do", r"are you (a )?(bot|ai|human)",
        r"நீ யார்", r"உன்னால என்ன செய்ய முடியும்",
        r"तुम कौन हो", r"आप कौन है", r"तुम क्या कर सकते हो",
    ]

    THANKS_PATTERNS = [
        r"\bthanks?\b", r"\bthank\s?you\b", r"\bthx\b", r"\bty\b",
        r"நன்றி", r"\bnandri\b",
        r"धन्यवाद", r"शुक्रिया", r"\bdhanyavaad\b", r"\bshukriya\b",
    ]

    GOODBYE_PATTERNS = [
        r"\bbye+\b", r"goodbye", r"see\s?you", r"talk\s?later", r"gotta go",
        r"போய் வரேன்", r"\bpoitu varen\b",
        r"अलविदा", r"फिर मिलेंगे", r"\bphir milenge\b",
    ]

    HELP_PATTERNS = [
        r"\bhelp\b", r"what all can (i|you)", r"what services",
        r"list.*(options|services|things)", r"menu",
        r"என்ன உதவி", r"என்னென்ன செய்யலாம்",
        r"क्या मदद", r"कौन कौन सी सुविधा",
    ]

    COMPLAINT_PATTERNS = [
        r"\bcomplain", r"\bescalate", r"speak to (a )?(human|agent|manager)",
        r"this is (useless|not working|frustrating)", r"terrible service",
        r"புகார்", r"பிரச்சனை", r"மனிதரிடம் பேச",
        r"शिकायत", r"इंसान से बात", r"मैनेजर से बात",
    ]

    SMALL_TALK_PATTERNS = [
        r"how are you", r"how('?s| is) it going", r"what'?s up",
        r"\bok(ay)?\b$", r"\balright\b",
        r"எப்படி இருக்க", r"நலமா",
        r"कैसे हो", r"क्या हाल है", r"\bkya haal hai\b",
    ]

    # ------------------------------------------------------------------
    # Mock General RAG knowledge base — stand-in for rag.py's General
    # collection. Keys are simple keyword triggers; real RAG will do
    # semantic retrieval over rag/data/general/ instead of this.
    # ------------------------------------------------------------------

    _MOCK_FAQ: Dict[str, Dict[str, str]] = {
        "capabilities": {
            "English": "I can help you check bills, explore or change plans, track payments and refunds, and troubleshoot network issues — just ask in English, Tamil, or Hindi.",
            "Tamil": "பில் பார்வையிட, திட்டங்களை மாற்ற, பணம்/திரும்பப்பெறுதல் நிலையை பார்க்க, நெட்வொர்க் சிக்கல்களை சரிசெய்ய உதவ முடியும்.",
            "Hindi": "मैं बिल देखने, प्लान बदलने, भुगतान/रिफंड ट्रैक करने और नेटवर्क समस्याएं ठीक करने में मदद कर सकता हूं।",
        },
        "hours": {
            "English": "I'm available anytime — I'm an automated assistant, not limited by business hours. For a human agent, availability may vary.",
            "Tamil": "நான் எப்போதும் கிடைக்கிறேன் — நான் ஒரு தானியங்கி உதவியாளர். மனிதர் உதவிக்கு நேரம் மாறுபடலாம்.",
            "Hindi": "मैं हमेशा उपलब्ध हूं — मैं एक स्वचालित सहायक हूं। इंसानी सहायता के लिए समय अलग हो सकता है।",
        },
        "languages": {
            "English": "Right now I support English, Tamil, and Hindi, with more Indian languages coming soon.",
            "Tamil": "தற்போது ஆங்கிலம், தமிழ், இந்தி ஆகியவற்றில் பேசலாம்; மேலும் மொழிகள் விரைவில்.",
            "Hindi": "अभी मैं अंग्रेज़ी, तमिल और हिंदी में मदद कर सकता हूं; जल्द ही और भाषाएं जुड़ेंगी।",
        },
    }

    _FAQ_KEYWORDS = {
        "capabilities": [r"what can", r"help.*with", r"services", r"என்ன", r"क्या मदद"],
        "hours": [r"\bhours?\b", r"\bavailable\b", r"open", r"நேரம்", r"समय"],
        "languages": [r"language", r"speak", r"மொழி", r"भाषा"],
    }

    def _init_(self, rag, tools, gemini):
        """
        Args:
            rag: existing rag.py instance/interface (used only when
                 general knowledge lookup is genuinely needed).
            tools: kept for interface consistency with other agents.
                   General Agent has no dedicated tool per the spec —
                   not used currently.
            gemini: existing gemini.py instance/interface, used for
                    natural-language response generation on fallback.
        """
        self.rag = rag
        self.tools = tools  # currently unused — no general_tool per spec
        self.gemini = gemini

    async def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point called by the orchestrator.

        Args:
            query: raw user query (any supported language)
            context: conversation context from context.py, e.g.
                {
                    "customer_id": "...",
                    "language": "Tamil",
                    "conversation_id": "abc123",
                    "history": [...],
                    "current_agent": "general"
                }

        Returns:
            {
                "agent": "general",
                "intent": str,
                "confidence": float,
                "used_rag": bool,
                "used_tool": bool,
                "response": str,
                "language": str,
                "escalate": bool
            }
        """
        language = context.get("language", "English")
        history = context.get("history", [])

        intent, confidence = self._detect_intent(query)
        logger.debug("GeneralAgent intent=%s confidence=%.2f query=%r", intent, confidence, query)

        escalate = False
        used_rag = False

        if intent == "greeting":
            response = self._pick(self._greeting_responses(language), history, "greeting")
        elif intent == "identity":
            response = self._pick(self._identity_responses(language), history, "identity")
        elif intent == "thanks":
            response = self._pick(self._thanks_responses(language), history, "thanks")
        elif intent == "goodbye":
            response = self._pick(self._goodbye_responses(language), history, "goodbye")
        elif intent == "small_talk":
            response = self._pick(self._small_talk_responses(language), history, "small_talk")
        elif intent == "help":
            response, used_rag = await self._handle_help(language)
        elif intent == "complaint":
            response = self._pick(self._complaint_responses(language), history, "complaint")
            escalate = True
        else:
            response, used_rag = await self._handle_fallback(query, context, language)

        return {
            "agent": "general",
            "intent": intent,
            "confidence": confidence,
            "used_rag": used_rag,
            "used_tool": False,
            "response": response,
            "language": language,
            "escalate": escalate,
        }

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(self, query: str) -> Tuple[str, float]:
        """
        Returns (intent, confidence). Confidence here is a simple mock
        heuristic (1.0 = pattern hit, 0.3 = no pattern hit / fallback).
        Replace with Supervisor's real classifier confidence once wired.
        """
        q = query.strip().lower()

        # Order matters: check more specific/urgent intents (complaint)
        # before generic small talk to avoid misrouting an angry user
        # into a "how are you" style response.
        ordered_checks = [
            ("complaint", self.COMPLAINT_PATTERNS),
            ("goodbye", self.GOODBYE_PATTERNS),
            ("thanks", self.THANKS_PATTERNS),
            ("help", self.HELP_PATTERNS),
            ("identity", self.IDENTITY_PATTERNS),
            ("greeting", self.GREETING_PATTERNS),
            ("small_talk", self.SMALL_TALK_PATTERNS),
        ]

        for intent_name, patterns in ordered_checks:
            if self._matches_any(q, patterns):
                return intent_name, 1.0

        return "fallback", 0.3

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    # ------------------------------------------------------------------
    # Response variety helper — avoids repeating the exact same line
    # twice in a row within the same conversation, using history from
    # context.py (read-only; does not maintain its own history store).
    # ------------------------------------------------------------------

    def _pick(self, options: List[str], history: List[Dict[str, Any]], tag: str) -> str:
        if not options:
            return ""
        if len(options) == 1:
            return options[0]

        last_response = None
        if history:
            for turn in reversed(history):
                if turn.get("agent") == "general" and turn.get("intent") == tag:
                    last_response = turn.get("response")
                    break

        choices = [o for o in options if o != last_response] or options
        return random.choice(choices)

    # ------------------------------------------------------------------
    # Response banks (multiple phrasings per language/intent)
    # ------------------------------------------------------------------

    def _greeting_responses(self, language: str) -> List[str]:
        bank = {
            "English": [
                "Hello! I'm your telecom assistant. How can I help — billing, plans, payments, or a network issue?",
                "Hi there! What can I help you with today — your bill, your plan, a payment, or your network?",
                "Hey! Good to hear from you. Are you calling about billing, plans, payments, or a network problem?",
            ],
            "Tamil": [
                "வணக்கம்! நான் உங்கள் டெலிகாம் உதவியாளர். பில், திட்டங்கள், பணம் செலுத்துதல் அல்லது நெட்வொர்க் சிக்கல் — எதில் உதவலாம்?",
                "வணக்கம்! இன்று என்ன உதவி வேண்டும் — பில், திட்டம், பணம் அல்லது நெட்வொர்க் தொடர்பானதா?",
            ],
            "Hindi": [
                "नमस्ते! मैं आपका टेलिकॉम सहायक हूं। बिलिंग, प्लान, भुगतान या नेटवर्क समस्या — मैं किसमें मदद कर सकता हूं?",
                "नमस्कार! आज मैं आपकी किस चीज़ में मदद करूं — बिल, प्लान, पेमेंट या नेटवर्क?",
            ],
        }
        return bank.get(language, bank["English"])

    def _identity_responses(self, language: str) -> List[str]:
        bank = {
            "English": [
                "I'm your AI voice assistant for telecom support — I handle bills, plans, payments, and network issues in English, Tamil, or Hindi.",
                "I'm an automated assistant here to help with billing, plans, payments, and connectivity problems.",
            ],
            "Tamil": [
                "நான் டெலிகாம் உதவிக்கான AI குரல் உதவியாளர் — பில், திட்டங்கள், பணம் செலுத்துதல் மற்றும் நெட்வொர்க் சிக்கல்களில் உதவ முடியும்.",
            ],
            "Hindi": [
                "मैं आपका टेलिकॉम सपोर्ट के लिए AI वॉइस असिस्टेंट हूं — बिल, प्लान, भुगतान और नेटवर्क समस्याओं में मदद कर सकता हूं।",
            ],
        }
        return bank.get(language, bank["English"])

    def _thanks_responses(self, language: str) -> List[str]:
        bank = {
            "English": [
                "You're welcome! Anything else I can help with?",
                "Happy to help! Let me know if there's more.",
            ],
            "Tamil": ["நல்லது! வேறு ஏதாவது உதவி வேண்டுமா?"],
            "Hindi": ["कोई बात नहीं! अगर कुछ और मदद चाहिए तो बताइए।"],
        }
        return bank.get(language, bank["English"])

    def _goodbye_responses(self, language: str) -> List[str]:
        bank = {
            "English": ["Goodbye! Have a great day.", "Take care! Reach out anytime."],
            "Tamil": ["போய் வாருங்கள்! நல்ல நாள் அமையட்டும்."],
            "Hindi": ["अलविदा! आपका दिन शुभ हो।"],
        }
        return bank.get(language, bank["English"])

    def _small_talk_responses(self, language: str) -> List[str]:
        bank = {
            "English": [
                "I'm doing well, thanks for asking! What can I help you with today?",
                "All good here! How can I assist you?",
            ],
            "Tamil": ["நான் நலமா இருக்கிறேன்! உங்களுக்கு என்ன உதவி வேண்டும்?"],
            "Hindi": ["मैं ठीक हूं, धन्यवाद! आज मैं आपकी कैसे मदद करूं?"],
        }
        return bank.get(language, bank["English"])

    def _complaint_responses(self, language: str) -> List[str]:
        bank = {
            "English": [
                "I'm sorry you're having a frustrating experience. I'm flagging this for a human agent to follow up — can you briefly tell me what happened?",
            ],
            "Tamil": ["உங்களுக்கு ஏற்பட்ட சிரமத்திற்கு வருந்துகிறேன். இதை ஒரு பிரதிநிதியிடம் தெரிவிக்கிறேன் — என்ன நடந்தது என்று சொல்ல முடியுமா?"],
            "Hindi": ["आपको हुई असुविधा के लिए क्षमा चाहता हूं। मैं इसे एक एजेंट तक पहुंचा रहा हूं — कृपया बताएं क्या हुआ?"],
        }
        return bank.get(language, bank["English"])

    # ------------------------------------------------------------------
    # Help / capabilities — uses mock FAQ RAG
    # ------------------------------------------------------------------

    async def _handle_help(self, language: str) -> Tuple[str, bool]:
        # TODO: replace with real rag.py call, e.g.:
        # result = await self.rag.query("what can you help with", domain="general", top_k=1)
        entry = self._MOCK_FAQ["capabilities"]
        return entry.get(language, entry["English"]), True

    # ------------------------------------------------------------------
    # Fallback path — mock RAG keyword match, then Gemini
    # ------------------------------------------------------------------

    async def _handle_fallback(
        self, query: str, context: Dict[str, Any], language: str
    ) -> Tuple[str, bool]:
        q = query.strip().lower()

        # Try mock FAQ keyword match first (stand-in for semantic RAG)
        for topic, patterns in self._FAQ_KEYWORDS.items():
            if self._matches_any(q, patterns):
                entry = self._MOCK_FAQ[topic]
                return entry.get(language, entry["English"]), True

        # TODO: replace with real rag.py semantic search over
        # rag/data/general/, e.g.:
        # rag_context = await self.rag.query(query, domain="general", top_k=3)
        rag_context = None

        # TODO: replace with real gemini.py call, e.g.:
        # response = await self.gemini.generate(
        #     query=query, context=context, rag_context=rag_context,
        #     system_prompt=GENERAL_AGENT_SYSTEM_PROMPT,
        # )
        response = await self._mock_gemini_generate(language)
        return response, rag_context is not None

    async def _mock_gemini_generate(self, language: str) -> str:
        bank = {
            "English": [
                "I'm not fully sure about that yet, but I can help with billing, plans, payments, or network issues. Could you tell me a bit more?",
                "I didn't quite catch that. I can help with bills, plans, payments, or network problems — which one fits?",
            ],
            "Tamil": ["அது பற்றி எனக்கு முழுமையாகத் தெரியவில்லை, ஆனால் பில், திட்டங்கள், பணம் செலுத்துதல் அல்லது நெட்வொர்க் சிக்கல்களில் உதவ முடியும். கொஞ்சம் விளக்கமாகச் சொல்ல முடியுமா?"],
            "Hindi": ["मुझे इसके बारे में पूरी जानकारी नहीं है, लेकिन मैं बिलिंग, प्लान, भुगतान या नेटवर्क समस्याओं में मदद कर सकता हूं। कृपया थोड़ा और बताएं?"],
        }
        options = bank.get(language, bank["English"])
        return random.choice(options)