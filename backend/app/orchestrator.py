"""
Orchestrator
File: backend/app/orchestrator.py

Coordinates the main processing flow of the multilingual GenAI voice assistant.

Responsibilities:
1. Accept customer queries and context
2. Route to specialized agents (via Supervisor)
3. Coordinate RAG retrieval and tool execution
4. Call Gemini for response generation
5. Validate confidence levels
6. Handle escalation to human agents
7. Maintain conversation history and context

Flow:

Customer Query
    ↓
Validation
    ↓
Session Context
    ↓
SupervisorAgent (classify request)
    ├─→ BillingAgent
    ├─→ PlansAgent
    ├─→ PaymentAgent
    ├─→ TechnicalAgent
    └─→ GeneralAgent
    ↓
RAG Retrieval (if needed)
    ↓
Tool Execution (if needed)
    ↓
Gemini Response Generation
    ↓
Confidence Evaluation
    ↓
Escalation Check
    ↓
Response
"""

import logging
from typing import Any, Dict, Optional

from backend.app.context import get_or_create_session
from backend.app.gemini import generate_text
from backend.app.rag import retrieve_context
from backend.app.validation import (
    validate_customer_query,
    validate_language,
    validate_session_id,
)
from backend.app.logger import get_logger

# Import agents
from backend.app.agents.supervisor_agent import SupervisorAgent
from backend.app.agents.billing_agent import BillingAgent
from backend.app.agents.plans_agent import PlansAgent
from backend.app.agents.payment_agent import PaymentAgent
from backend.app.agents.technical_agent import TechnicalAgent
from backend.app.agents.general_agent import GeneralAgent

logger = get_logger(__name__)


# ============================================================
# Agent Registry
# ============================================================

class Orchestrator:
    """
    Coordinates the main processing flow of the
    multilingual GenAI voice assistant.
    """

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.logger = logger
        
        # Initialize agents lazily to avoid circular dependencies
        self.agents = {
            "general": GeneralAgent(),
            # Other agents initialized on first use
        }

    def _get_agent(self, agent_name: str):
        """Get or lazily initialize an agent."""
        
        if agent_name in self.agents:
            return self.agents[agent_name]
        
        # Lazy initialization of specialized agents with dependencies
        if agent_name == "billing":
            from backend.app.rag import rag_service
            from backend.app import tools
            agent = BillingAgent(rag=rag_service, tools=tools, gemini=generate_text)
        elif agent_name == "plans":
            from backend.app.rag import rag_service
            from backend.app import tools
            agent = PlansAgent(rag=rag_service, tools=tools, gemini=generate_text)
        elif agent_name == "payment":
            from backend.app.rag import rag_service
            from backend.app import tools
            agent = PaymentAgent(rag=rag_service, tools=tools, gemini=generate_text)
        elif agent_name == "technical":
            from backend.app.rag import rag_service
            from backend.app import tools
            agent = TechnicalAgent(rag=rag_service, tools=tools, gemini=generate_text)
        else:
            agent = GeneralAgent()
        
        self.agents[agent_name] = agent
        return agent

    # ========================================================
    # MAIN ENTRY POINT
    # ========================================================

    async def process_text(
        self,
        session_id: str,
        customer_query: str,
        language: str = "en",
        customer_id: Optional[str] = None,
        nlu_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer text request end-to-end.

        Flow:
            Customer Query
                ↓
            Validation
                ↓
            Session Context
                ↓
            SupervisorAgent (classification)
                ↓
            Specialized Agent (handling)
                ↓
            RAG + Tool Execution
                ↓
            Gemini Response
                ↓
            Confidence Evaluation
                ↓
            Escalation Check
                ↓
            Response

        Returns:
            {
                "session_id": "...",
                "language": "en",
                "response": "Your response here...",
                "confidence": 0.95,
                "intent": "billing",
                "escalated": False,
                "rag_context": {...},
                "tool_result": {...},
                "escalation_reason": None,
            }
        """

        # ====================================================
        # VALIDATE INPUT
        # ====================================================

        try:
            session_id = validate_session_id(session_id)
            customer_query = validate_customer_query(customer_query)
            language = validate_language(language)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "session_id": session_id,
                "language": language,
                "response": "Invalid request parameters.",
                "confidence": 0.0,
                "intent": "error",
                "escalated": False,
                "rag_context": None,
                "tool_result": None,
                "escalation_reason": "Invalid input",
            }

        # ====================================================
        # GET OR CREATE SESSION
        # ====================================================

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

        logger.info(
            f"Processing query: session={session_id}, language={language}, "
            f"query_len={len(customer_query)}"
        )

        # ====================================================
        # PREPARE NLU DATA
        # ====================================================

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

        # ====================================================
        # CLASSIFY WITH SUPERVISOR
        # ====================================================

        logger.info("Running Supervisor classification...")

        supervisor_result = await self.supervisor.handle(
            query=customer_query,
            context={
                "session_id": session_id,
                "language": language,
                "customer_id": customer_id,
            },
        )

        agent_name = supervisor_result.get("agent", "general")
        supervisor_confidence = supervisor_result.get("confidence", 0.0)
        supervisor_method = supervisor_result.get("method", "fallback")

        logger.info(
            f"Supervisor routed to: {agent_name} "
            f"(confidence: {supervisor_confidence}, method: {supervisor_method})"
        )

        # ====================================================
        # GET SPECIALIZED AGENT
        # ====================================================

        agent = self._get_agent(agent_name)

        # ====================================================
        # DELEGATE TO AGENT
        # ====================================================

        logger.info(f"Delegating to {agent.__class__.__name__}...")

        agent_result = await agent.handle(
            query=customer_query,
            language=language,
            customer_id=customer_id,
            session_id=session_id,
            nlu_data=nlu_data,
        )

        # Extract agent outputs
        rag_context = agent_result.get("rag_context", {})
        tool_result = agent_result.get("tool_result", None)
        agent_confidence = agent_result.get("confidence", 0.5)

        # ====================================================
        # BUILD GEMINI PROMPT
        # ====================================================

        logger.info("Building Gemini prompt...")

        prompt = self._build_prompt(
            customer_query=customer_query,
            language=language,
            agent_name=agent_name,
            rag_result=rag_context,
            tool_result=tool_result,
            context=context,
        )

        # ====================================================
        # GENERATE RESPONSE WITH GEMINI
        # ====================================================

        logger.info("Generating response with Gemini...")

        try:
            response = await generate_text(prompt)
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            response = (
                "I apologize, but I'm unable to process your request at the moment. "
                "Please try again or contact our support team."
            )
            agent_confidence = 0.0

        # Store assistant response
        context.add_message(
            role="assistant",
            content=response,
            language=language,
        )

        # ====================================================
        # ESCALATION CHECK
        # ====================================================

        logger.info("Checking escalation conditions...")

        escalation_required = self._should_escalate(
            confidence=agent_confidence,
            intent=agent_name,
            tool_result=tool_result,
            query=customer_query,
        )

        escalation_reason = None
        if escalation_required:
            escalation_reason = self._get_escalation_reason(
                confidence=agent_confidence,
                intent=agent_name,
                tool_result=tool_result,
            )
            logger.warning(f"Escalation triggered: {escalation_reason}")

        # ====================================================
        # BUILD FINAL RESPONSE
        # ====================================================

        final_response = {
            "session_id": session_id,
            "language": language,
            "response": response,
            "confidence": agent_confidence,
            "intent": agent_name,
            "escalated": escalation_required,
            "rag_context": rag_context,
            "tool_result": tool_result,
            "escalation_reason": escalation_reason,
        }

        logger.info(
            f"Query processed: confidence={agent_confidence}, "
            f"escalated={escalation_required}"
        )

        return final_response

    # ========================================================
    # HELPER METHODS
    # ========================================================

    def _build_prompt(
        self,
        customer_query: str,
        language: str,
        agent_name: str,
        rag_result: Any,
        tool_result: Any,
        context: Any,
    ) -> str:
        """
        Build the prompt sent to Gemini.
        """

        history = context.get_history()
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in history[-10:]  # Last 10 messages
        ])

        rag_text = ""
        if rag_result and rag_result.get("retrieved_context"):
            rag_text = "\n".join([
                f"- {doc.get('source', 'Unknown')}: {doc.get('content', '')}"
                for doc in rag_result.get("retrieved_context", [])[:3]
            ])

        tool_text = ""
        if tool_result:
            tool_text = f"Retrieved Information: {tool_result}"

        prompt = f"""
You are a multilingual telecom customer-care assistant.

LANGUAGE: {language.upper()}
AGENT TYPE: {agent_name.upper()}
CUSTOMER QUERY: {customer_query}

CONVERSATION HISTORY (last 10 messages):
{history_text if history_text else "No previous context"}

{"RETRIEVED KNOWLEDGE BASE:" + rag_text if rag_text else ""}

{"CUSTOMER ACCOUNT INFORMATION:" + tool_text if tool_text else ""}

RULES:
1. Respond in the customer's language ({language}).
2. Answer using only the provided information.
3. If knowledge base or account data is insufficient, indicate that
   the information needs to be verified or that you cannot help.
4. Keep responses concise and professional.
5. Ask clarification questions if needed.
6. Do not invent customer account or billing information.
7. For sensitive issues or escalations, offer to connect with a human agent.

RESPONSE:
"""

        return prompt

    def _should_escalate(
        self,
        confidence: float,
        intent: str,
        tool_result: Any,
        query: str,
    ) -> bool:
        """
        Determine whether the request should be escalated
        to a human agent.

        Escalation triggers:
        - Confidence < 0.60
        - Tool execution failed
        - Customer requests escalation
        - Sensitive/security issues
        """

        # Low confidence
        if confidence < 0.60:
            return True

        # Tool failure
        if tool_result and not tool_result.get("success", False):
            return True

        # Customer requests escalation
        escalation_keywords = [
            "escalate",
            "human",
            "agent",
            "manager",
            "supervisor",
            "complaint",
            "dissatisfied",
        ]
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True

        return False

    def _get_escalation_reason(
        self,
        confidence: float,
        intent: str,
        tool_result: Any,
    ) -> str:
        """
        Get a human-readable reason for escalation.
        """

        if confidence < 0.60:
            return f"Low confidence ({confidence:.2f}) - requires human review"

        if tool_result and not tool_result.get("success", False):
            return f"Tool execution failed: {tool_result.get('error', 'Unknown error')}"

        return "Customer requested escalation"


# ============================================================
# SHARED ORCHESTRATOR INSTANCE
# ============================================================

orchestrator = Orchestrator()
