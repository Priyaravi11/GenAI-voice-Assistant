"""
Session Context
File: backend/app/context.py

Manages all information related to an active customer session.

Responsibilities:
- Store session information (ID, customer ID, language)
- Store conversation history (messages)
- Store session data (extracted information)
- Track pending Customer-ID requests
- Manage session lifecycle
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SessionContext:
    """
    Stores all information related to an active customer session.

    Responsibilities:
        - Store session information
        - Store customer ID
        - Store conversation history
        - Store language and status
        - Store pending Customer-ID request state
        - Track whether system is waiting for Customer ID

    Pending Customer-ID Flow Example:

        Customer: "What is my current bill?"
        Agent: Customer ID is required.

        Session stores:
            waiting_for_customer_id = True
            pending_agent = "billing"
            pending_query = "What is my current bill?"
            pending_tool = "get_current_bill"
            pending_nlu_data = {...}

        Customer: "C251"
        Orchestrator: Resumes pending request with customer ID
    """

    def __init__(
        self,
        session_id: str,
        customer_id: Optional[str] = None,
        language: str = "en",
    ):
        # =====================================================
        # BASIC SESSION INFORMATION
        # =====================================================

        self.session_id = session_id
        self.customer_id = customer_id
        self.language = language
        self.status = "active"

        # =====================================================
        # TIMESTAMPS
        # =====================================================

        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

        # =====================================================
        # CONVERSATION HISTORY
        # =====================================================

        self.messages: list[Dict[str, Any]] = []

        # =====================================================
        # SESSION DATA
        # =====================================================
        # Stores extracted/useful information from interactions
        # Examples: plan_id, area, payment method, etc.
        # =====================================================

        self.data: Dict[str, Any] = {}

        # =====================================================
        # PENDING CUSTOMER-ID REQUEST STATE
        # =====================================================
        # Used when a customer-specific operation requires
        # customer_id but the customer has not provided it yet.
        # =====================================================

        self.waiting_for_customer_id: bool = False
        self.pending_agent: Optional[str] = None
        self.pending_query: Optional[str] = None
        self.pending_tool: Optional[str] = None
        self.pending_nlu_data: Optional[Dict[str, Any]] = None

    # ==========================================================
    # MESSAGE MANAGEMENT
    # ==========================================================

    def add_message(
        self,
        role: str,
        content: str,
        **metadata: Any,
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "customer", "assistant", or "system"
            content: Message text
            **metadata: Additional fields (language, agent, etc.)
        """

        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **metadata,
            }
        )

        self.updated_at = datetime.now(timezone.utc)

    # ==========================================================
    # SESSION UPDATE
    # ==========================================================

    def update(self, **values: Any) -> None:
        """
        Update session attributes or session data.

        Known SessionContext attributes are updated directly.
        Unknown fields are stored inside self.data.

        Example:
            context.update(customer_id="C251", area="NYC")
        """

        for key, value in values.items():

            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.data[key] = value

        self.updated_at = datetime.now(timezone.utc)

    # ==========================================================
    # PENDING CUSTOMER-ID REQUEST MANAGEMENT
    # ==========================================================

    def set_pending_customer_id_request(
        self,
        agent: str,
        query: str,
        tool_name: Optional[str] = None,
        nlu_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a request that is waiting for Customer ID.

        Called when an agent determines a tool requires
        customer_id but it's not available.

        Args:
            agent: Agent name (e.g., "billing")
            query: Original customer query to resume
            tool_name: Tool that requires the customer ID
            nlu_data: NLU data to pass when resuming
        """

        self.waiting_for_customer_id = True
        self.pending_agent = agent
        self.pending_query = query
        self.pending_tool = tool_name
        self.pending_nlu_data = nlu_data
        self.updated_at = datetime.now(timezone.utc)

    def get_pending_request(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve pending request details if waiting for customer ID.

        Returns:
            Dictionary with pending request info or None if not waiting.
        """

        if not self.waiting_for_customer_id:
            return None

        return {
            "pending_agent": self.pending_agent,
            "pending_query": self.pending_query,
            "pending_tool": self.pending_tool,
            "pending_nlu_data": self.pending_nlu_data,
        }

    def clear_pending_customer_id_request(
        self,
    ) -> None:
        """
        Clear the pending customer-ID request after the customer ID
        has been received and the request has been resumed.
        """

        self.waiting_for_customer_id = False
        self.pending_agent = None
        self.pending_query = None
        self.pending_tool = None
        self.pending_nlu_data = None
        self.updated_at = datetime.now(timezone.utc)

    # ==========================================================
    # CONVERSATION HISTORY
    # ==========================================================

    def get_history(self) -> list[Dict[str, Any]]:
        """
        Return complete conversation history.
        """

        return self.messages

    # ==========================================================
    # SESSION DATA
    # ==========================================================

    def get_data(self) -> Dict[str, Any]:
        """
        Return additional session data.
        """

        return self.data

    # ==========================================================
    # CLOSE SESSION
    # ==========================================================

    def close(self) -> None:
        """
        Close the current session.
        """

        self.status = "closed"
        self.updated_at = datetime.now(timezone.utc)


# =============================================================
# ACTIVE SESSIONS (In-Memory Storage)
# =============================================================

_sessions: Dict[str, SessionContext] = {}


# =============================================================
# CREATE SESSION
# =============================================================

def create_session(
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en",
) -> SessionContext:
    """
    Create and register a new session.

    Args:
        session_id: Unique session identifier
        customer_id: Optional customer ID
        language: Language code (default: "en")

    Returns:
        New SessionContext instance
    """

    context = SessionContext(
        session_id=session_id,
        customer_id=customer_id,
        language=language,
    )

    _sessions[session_id] = context

    return context


# =============================================================
# GET SESSION
# =============================================================

def get_session(
    session_id: str,
) -> Optional[SessionContext]:
    """
    Retrieve an existing session.

    Args:
        session_id: Session identifier

    Returns:
        SessionContext if found, None if session does not exist
    """

    return _sessions.get(session_id)


# =============================================================
# GET OR CREATE SESSION
# =============================================================

def get_or_create_session(
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en",
) -> SessionContext:
    """
    Return an existing session or create a new one.

    Important:
        If the session already exists, its existing customer_id
        and pending request state are preserved.

    Args:
        session_id: Session identifier
        customer_id: Customer ID (only used if session is new)
        language: Language code (updated if session exists)

    Returns:
        SessionContext (new or existing)
    """

    existing_session = get_session(session_id)

    if existing_session:
        # Update customer ID only if not already set
        if customer_id and not existing_session.customer_id:
            existing_session.customer_id = customer_id
            existing_session.updated_at = datetime.now(timezone.utc)

        # Update language if provided
        if language:
            existing_session.language = language
            existing_session.updated_at = datetime.now(timezone.utc)

        return existing_session

    return create_session(
        session_id=session_id,
        customer_id=customer_id,
        language=language,
    )


# =============================================================
# REMOVE SESSION
# =============================================================

def remove_session(
    session_id: str,
) -> bool:
    """
    Remove an active session.

    Args:
        session_id: Session identifier

    Returns:
        True if session was removed, False if it didn't exist
    """

    if session_id in _sessions:
        del _sessions[session_id]
        return True

    return False
