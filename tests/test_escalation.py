"""
Test script for escalation.py
File: backend/app/test_escalate.py

Run:
    python test_escalate.py

No Twilio, no network calls, no credentials, no gemini.py needed —
pure logic test covering all 6 languages from gemini.py's
SUPPORTED_LANGUAGES list.
"""

from escalation import EscalationManager

LANGUAGES_TO_TEST = ["English", "Tamil", "Hindi", "Telugu", "Kannada", "Malayalam"]


def run_test(name, agent_result, context):
    print(f"\n--- {name} ---")
    manager = EscalationManager()

    escalate = manager.should_escalate(agent_result)
    print(f"should_escalate -> {escalate}")

    if escalate:
        result = manager.handle_escalation(
            reason=agent_result.get("intent", "unspecified"),
            context=context,
        )
        print("Response shown to user:")
        print(result["response"])
        print(f"(language: {result['language']}, reason: {result['reason']})")
    else:
        print("No escalation triggered — normal agent response would be shown instead.")


def main():
    # One test per supported language
    for lang in LANGUAGES_TO_TEST:
        run_test(
            f"Escalate - {lang}",
            agent_result={"agent": "billing", "intent": "no_answer_found", "escalate": True},
            context={"language": lang},
        )

    # Missing language key -> should default to English
    run_test(
        "Escalate - no language key (defaults to English)",
        agent_result={"agent": "general", "intent": "fallback", "escalate": True},
        context={},
    )

    # Unrecognized language value -> should default to English
    run_test(
        "Escalate - unrecognized language (defaults to English)",
        agent_result={"agent": "technical", "intent": "no_answer_found", "escalate": True},
        context={"language": "French"},
    )

    # No escalation needed
    run_test(
        "No escalation needed",
        agent_result={"agent": "plans", "intent": "plan_info", "escalate": False},
        context={"language": "English"},
    )


if __name__ == "__main__":
    main()