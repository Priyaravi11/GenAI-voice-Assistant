"""
Orchestrator (Improved)
File: backend/app/orchestrator_improved.py

Central orchestration layer for the multilingual GenAI Telecom Voice Assistant.

Responsibilities:
1. Create/retrieve conversation sessions
2. Maintain SessionContext
3. Pass customer_id and language to agents
4. Send customer's query to SupervisorAgent
5. Route query to correct specialized agent
6. Handle pending Customer-ID requests
7. Store conversation history
8. Return standardized response structure

Flow:
    User Query
        ↓
    Validate Input
        ↓
    Get/Create Session
        ↓
    Check Pending Customer-ID Request
        ├─ (if waiting) Handle Customer ID Input
        └─ (if not) Normal Flow
        ↓
    SupervisorAgent Classification
        ↓
    Specialized Agent Execution
        ↓
    Check requires_customer_id Signal
        ├─ (if true) Store Pending State & Ask for ID
        └─ (if false) Continue
        ↓
    Generate Response
        ↓
    Escalation Check
        ↓
    Return Response
"""

from typing import Any, Dict, Optional
import logging

from backend.app.context import get_or_create_session, get_session
from backend.app.customer_validation import validate_customer_id
from backend.app.logger import get_logger
from backend.app import tools as tool_registry

# Import Supervisor
from backend.app.agents.supervisor_agent import SupervisorAgent

# Import Specialized Agents
from backend.app.agents.billing_agent import BillingAgent
from backend.app.agents.plans_agent import PlansAgent
from backend.app.agents.payment_agent import PaymentAgent
from backend.app.agents.technical_agent import TechnicalAgent
from backend.app.agents.general_agent import GeneralAgent

logger = get_logger(__name__)
# Import RAG Service if available
try:
    from rag.retrieval.retriever import Retriever
    rag_service = Retriever()
except Exception as e:
    logger.warning(f"RAG service unavailable, using fallback: {str(e)}")
    rag_service = None


class Orchestrator:
    """
    Central orchestration layer for the multilingual GenAI voice assistant.
    """

    def __init__(self):
        """Initialize orchestrator with supervisor and specialized agents."""
        
        self.supervisor = SupervisorAgent()
        self.logger = logger

        # Initialize agents
        self.agents = {
            "general": GeneralAgent(),
            "billing": BillingAgent(),
            "plans": PlansAgent(
                rag=rag_service,
                tools=tool_registry,
                gemini=None,
            ),
            "payment": PaymentAgent(),
            "technical": TechnicalAgent(
                rag=rag_service,
                tools=tool_registry,
                gemini=None,
            ),
        }

    # ====================================================================
    # MAIN ENTRY POINT
    # ====================================================================

    async def handle(
        self,
        query: str,
        session_id: str,
        customer_id: Optional[str] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process one customer request end-to-end.

        Args:
            query: Customer's current message.
            session_id: Unique conversation/session ID.
            customer_id: Customer ID if already known.
            language: Customer language code (e.g., "en", "ta", "hi").

        Returns:
            Standard orchestrator response with:
            - response: Main response text
            - confidence: Confidence level (0.0-1.0)
            - agent: Which agent handled it
            - intent: Classified intent
            - requires_customer_id: Whether customer ID is needed
            - escalated: Whether escalation triggered
            - tool_result: Any tool output
            - rag_context: Any RAG context
        """

        # ================================================================
        # VALIDATE INPUT
        # ================================================================

        if not session_id or not isinstance(session_id, str):
            logger.error("Invalid session ID")
            return self._error_response("Invalid session ID.")

        if not isinstance(query, str):
            logger.error("Invalid query type")
            return self._error_response("Invalid query type.")

        query = query.strip()

        if not query:
            logger.error("Empty query")
            return self._error_response("Please provide a message.")

        if not isinstance(language, str):
            language = "en"

        language = language.lower().strip()

        # ================================================================
        # GET OR CREATE SESSION
        # ================================================================

        context = get_or_create_session(
            session_id=session_id,
            customer_id=customer_id,
            language=language,
        )

        logger.info(
            f"Processing: session={session_id} | "
            f"language={language} | query_len={len(query)}"
        )

        # ================================================================
        # CHECK FOR PENDING CUSTOMER-ID REQUEST
        # ================================================================
        # CRITICAL: If waiting for Customer ID, don't classify with
        # Supervisor. Use current message as Customer ID input.
        # ================================================================

        if context.waiting_for_customer_id:
            logger.info(
                f"Session {session_id} waiting for Customer ID. "
                f"Processing message as ID input."
            )

            return await self._handle_customer_id_input(
                session_id=session_id,
                customer_id_input=query,
                language=language,
                context=context,
            )

        # ================================================================
        # STORE USER MESSAGE
        # ================================================================

        context.add_message(
            role="user",
            content=query,
        )

        # ================================================================
        # BUILD AGENT CONTEXT
        # ================================================================

        agent_context = self._build_agent_context(context)

        # ================================================================
        # SUPERVISOR CLASSIFICATION
        # ================================================================

        logger.info("Running Supervisor classification...")

        supervisor_result = await self.supervisor.handle(
            query=query,
            context=agent_context,
        )

        agent_name = supervisor_result.get("agent", "general").lower()
        supervisor_confidence = supervisor_result.get("confidence", 0.0)

        # Safety check
        if agent_name not in self.agents:
            agent_name = "general"

        logger.info(
            f"Supervisor routed to: {agent_name} "
            f"(confidence: {supervisor_confidence})"
        )

        # ================================================================
        # GET SPECIALIZED AGENT
        # ================================================================

        agent = self.agents.get(agent_name)

        if agent is None:
            logger.error(f"Agent not found: {agent_name}")
            return self._error_response(
                "Unable to find the appropriate assistant."
            )

        # ================================================================
        # EXECUTE SPECIALIZED AGENT
        # ================================================================

        logger.info(f"Delegating to {agent.__class__.__name__}...")

        try:
            agent_result = await agent.handle(
                query=query,
                context=agent_context,
            )

        except Exception as exc:
            logger.exception(f"Agent execution failed: {str(exc)}")

            context.add_message(
                role="system",
                content=f"{agent_name} agent execution failed.",
                error=str(exc),
            )

            return self._error_response(
                "I'm sorry, I couldn't process your request right now."
            )

        # ================================================================
        # CHECK FOR REQUIRES_CUSTOMER_ID SIGNAL
        # ================================================================
        # If agent returns requires_customer_id=True, store pending
        # state and ask for Customer ID instead of continuing.
        # ================================================================

        if agent_result.get("requires_customer_id", False):
            logger.info(
                f"Agent {agent_name} requires Customer ID. "
                f"Storing pending state."
            )

            tool_name = agent_result.get("tool_used")
            response_text = agent_result.get(
                "response",
                "Please provide your customer ID.",
            )

            # Store pending request
            context.set_pending_customer_id_request(
                agent=agent_name,
                query=query,
                tool=tool_name,
            )

            # Store assistant message
            context.add_message(
                role="assistant",
                content=response_text,
            )

            return {
                "session_id": session_id,
                "customer_id": context.customer_id,
                "language": language,
                "agent": agent_name,
                "confidence": 1.0,
                "reason": "Waiting for Customer ID",
                "method": "pending_customer_id",
                "used_rag": False,
                "used_tool": False,
                "tool_name": tool_name,
                "rag_context": {},
                "tool_data": None,
                "response": response_text,
                "requires_customer_id": True,
                "escalated": False,
                "escalation_reason": None,
            }

        # ================================================================
        # NORMAL FLOW: Extract agent outputs
        # ================================================================

        response_text = agent_result.get("response", "")

        if not response_text:
            logger.warning("Agent returned empty response")
            response_text = (
                "I'm sorry, I couldn't generate a response for your request."
            )

        # Store assistant message
        context.add_message(
            role="assistant",
            content=response_text,
            agent=agent_name,
        )

        # ================================================================
        # ESCALATION CHECK
        # ================================================================

        agent_confidence = agent_result.get("confidence", 0.5)
        tool_result = agent_result.get("tool_result")

        escalation_required = self._should_escalate(
            confidence=agent_confidence,
            agent_name=agent_name,
            tool_result=tool_result,
            query=query,
        )

        escalation_reason = None
        if escalation_required:
            escalation_reason = self._get_escalation_reason(
                confidence=agent_confidence,
                agent_name=agent_name,
                tool_result=tool_result,
            )

        # ================================================================
        # RETURN RESPONSE
        # ================================================================

        return {
            "session_id": session_id,
            "customer_id": context.customer_id,
            "language": language,
            "agent": agent_name,
            "confidence": agent_confidence,
            "reason": supervisor_result.get("reason", ""),
            "method": supervisor_result.get("method", "gemini"),
            "used_rag": bool(agent_result.get("rag_context")),
            "used_tool": agent_result.get("tool_used") is not None,
            "tool_name": agent_result.get("tool_used"),
            "rag_context": agent_result.get("rag_context", {}),
            "tool_data": tool_result,
            "response": response_text,
            "requires_customer_id": False,
            "escalated": escalation_required,
            "escalation_reason": escalation_reason,
        }

    async def process_text(
        self,
        session_id: str,
        customer_query: str,
        language: str = "en",
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compatibility wrapper used by the WebSocket layer.
        """

        return await self.handle(
            query=customer_query,
            session_id=session_id,
            customer_id=customer_id,
            language=language,
        )

    # ====================================================================
    # HANDLE CUSTOMER ID INPUT
    # ====================================================================

    async def _handle_customer_id_input(
        self,
        session_id: str,
        customer_id_input: str,
        language: str,
        context: Any,
    ) -> Dict[str, Any]:
        """
        Handle customer ID input when session is waiting for it.

        Flow:
        1. Validate the customer ID
        2. Store it in session context
        3. Retrieve pending request details
        4. Resume the pending request
        5. Execute tool with customer ID
        6. Generate response
        7. Clear pending state
        """

        # ================================================================
        # VALIDATE CUSTOMER ID
        # ================================================================

        is_valid, error_msg, normalized_id = validate_customer_id(
            customer_id_input,
            allow_none=False,
        )

        if not is_valid:
            logger.warning(f"Invalid customer ID: {error_msg}")

            context.add_message(
                role="user",
                content=customer_id_input,
            )

            response_text = (
                f"Invalid customer ID. {error_msg} "
                f"Please provide your customer ID."
            )

            context.add_message(
                role="assistant",
                content=response_text,
            )

            # Keep waiting
            return {
                "session_id": session_id,
                "customer_id": context.customer_id,
                "language": language,
                "agent": "general",
                "confidence": 0.0,
                "reason": "Invalid Customer ID",
                "method": "customer_id_validation",
                "used_rag": False,
                "used_tool": False,
                "tool_name": None,
                "rag_context": {},
                "tool_data": None,
                "response": response_text,
                "requires_customer_id": True,
                "escalated": False,
                "escalation_reason": None,
            }

        # ================================================================
        # STORE CUSTOMER ID
        # ================================================================

        logger.info(f"Storing Customer ID for session {session_id}")

        context.customer_id = normalized_id
        context.update(customer_id=normalized_id)

        # ================================================================
        # RETRIEVE PENDING REQUEST
        # ================================================================

        pending_request = context.get_pending_customer_id_request()

        if not pending_request.get("waiting_for_customer_id"):
            logger.error(f"No pending request for session {session_id}")

            return self._error_response(
                "I'm sorry, but I cannot process your request right now."
            )

        # ================================================================
        # RESUME PENDING REQUEST
        # ================================================================

        pending_agent = pending_request.get("agent")
        pending_query = pending_request.get("query")
        pending_tool = pending_request.get("tool")

        logger.info(
            f"Resuming pending {pending_agent} request "
            f"for session {session_id}"
        )

        # Store user's customer ID input
        context.add_message(
            role="user",
            content=customer_id_input,
        )

        # ================================================================
        # GET AGENT AND EXECUTE
        # ================================================================

        agent = self.agents.get(pending_agent, self.agents["general"])

        agent_context = self._build_agent_context(context)

        try:
            agent_result = await agent.handle(
                query=pending_query,
                context=agent_context,
            )

        except Exception as exc:
            logger.exception(f"Resumed agent execution failed: {str(exc)}")

            return self._error_response(
                "I'm sorry, I encountered an error processing your request."
            )

        # ================================================================
        # CHECK IF STILL REQUIRES CUSTOMER ID (shouldn't happen)
        # ================================================================

        if agent_result.get("requires_customer_id", False):
            logger.error(
                f"Agent {pending_agent} still requires Customer ID "
                f"after it was provided!"
            )

            return self._error_response(
                "I'm sorry, but I encountered an issue processing your "
                "request. Please try again."
            )

        # ================================================================
        # GENERATE FINAL RESPONSE
        # ================================================================

        response_text = agent_result.get(
            "response",
            "Your request has been processed.",
        )

        agent_confidence = agent_result.get("confidence", 0.5)
        tool_result = agent_result.get("tool_result")

        # Store assistant response
        context.add_message(
            role="assistant",
            content=response_text,
            agent=pending_agent,
        )

        # ================================================================
        # ESCALATION CHECK
        # ================================================================

        escalation_required = self._should_escalate(
            confidence=agent_confidence,
            agent_name=pending_agent,
            tool_result=tool_result,
            query=pending_query,
        )

        escalation_reason = None
        if escalation_required:
            escalation_reason = self._get_escalation_reason(
                confidence=agent_confidence,
                agent_name=pending_agent,
                tool_result=tool_result,
            )

        # ================================================================
        # CLEAR PENDING STATE
        # ================================================================

        context.clear_pending_customer_id_request()

        logger.info(f"Cleared pending Customer ID request for {session_id}")

        # ================================================================
        # RETURN FINAL RESPONSE
        # ================================================================

        return {
            "session_id": session_id,
            "customer_id": context.customer_id,
            "language": language,
            "agent": pending_agent,
            "confidence": agent_confidence,
            "reason": f"Resumed {pending_agent} request with Customer ID",
            "method": "customer_id_resume",
            "used_rag": bool(agent_result.get("rag_context")),
            "used_tool": agent_result.get("tool_used") is not None,
            "tool_name": agent_result.get("tool_used"),
            "rag_context": agent_result.get("rag_context", {}),
            "tool_data": tool_result,
            "response": response_text,
            "requires_customer_id": False,
            "escalated": escalation_required,
            "escalation_reason": escalation_reason,
        }

    # ====================================================================
    # BUILD AGENT CONTEXT
    # ====================================================================

    def _build_agent_context(
        self,
        context: Any,
    ) -> Dict[str, Any]:
        """
        Convert SessionContext into dictionary format for agents.
        """

        return {
            "session_id": context.session_id,
            "customer_id": context.customer_id,
            "language": context.language,
            "status": context.status,
            "history": context.get_history(),
            **context.get_data(),
        }

    # ====================================================================
    # ESCALATION CHECKS
    # ====================================================================

    def _should_escalate(
        self,
        confidence: float,
        agent_name: str,
        tool_result: Any,
        query: str,
    ) -> bool:
        """
        Determine whether escalation to human agent is needed.
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
        ]
        if any(keyword in query.lower() for keyword in escalation_keywords):
            return True

        return False

    def _get_escalation_reason(
        self,
        confidence: float,
        agent_name: str,
        tool_result: Any,
    ) -> str:
        """
        Get human-readable escalation reason.
        """

        if confidence < 0.60:
            return f"Low confidence ({confidence:.2f}) in {agent_name} response"

        if tool_result and not tool_result.get("success", False):
            error = (
                tool_result.get("error")
                or tool_result.get("message")
                or "The support tool could not complete the lookup."
            )
            return f"Tool execution failed: {error}"

        return "Escalation requested"

    # ====================================================================
    # ERROR RESPONSE
    # ====================================================================

    @staticmethod
    def _error_response(
        message: str,
    ) -> Dict[str, Any]:
        """
        Standard error response.
        """

        return {
            "session_id": None,
            "customer_id": None,
            "language": "en",
            "agent": "general",
            "confidence": 0.0,
            "reason": message,
            "method": "error",
            "used_rag": False,
            "used_tool": False,
            "tool_name": None,
            "rag_context": {},
            "tool_data": None,
            "response": message,
            "requires_customer_id": False,
            "escalated": False,
            "escalation_reason": None,
        }

    # ====================================================================
    # SESSION MANAGEMENT
    # ====================================================================

    def get_session(
        self,
        session_id: str,
    ) -> Optional[Any]:
        """
        Retrieve an existing session.
        """

        return get_session(session_id)

    def close_session(
        self,
        session_id: str,
    ) -> bool:
        """
        Close an existing session.
        """

        context = get_session(session_id)

        if context is None:
            return False

        context.close()
        logger.info(f"Session closed: {session_id}")

        return True


# ========================================================================
# SHARED ORCHESTRATOR INSTANCE
# ========================================================================

orchestrator = Orchestrator()
