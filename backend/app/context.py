from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SessionContext:
    def __init__(
        self,
        session_id: str,
        customer_id: Optional[str] = None,
        language: str = "en",
    ):
        self.session_id = session_id
        self.customer_id = customer_id
        self.language = language
        self.status = "active"

        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

        self.messages: list[Dict[str, Any]] = []
        self.data: Dict[str, Any] = {}

    def add_message(
        self,
        role: str,
        content: str,
        **metadata: Any,
    ) -> None:
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **metadata,
            }
        )

        self.updated_at = datetime.now(timezone.utc)

    def update(self, **values: Any) -> None:
        for key, value in values.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.data[key] = value

        self.updated_at = datetime.now(timezone.utc)

    def get_history(self) -> list[Dict[str, Any]]:
        return self.messages

    def get_data(self) -> Dict[str, Any]:
        return self.data

    def close(self) -> None:
        self.status = "closed"
        self.updated_at = datetime.now(timezone.utc)


# Active sessions stored in memory
_sessions: Dict[str, SessionContext] = {}


def create_session(
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en",
) -> SessionContext:

    context = SessionContext(
        session_id=session_id,
        customer_id=customer_id,
        language=language,
    )

    _sessions[session_id] = context

    return context


def get_session(session_id: str) -> Optional[SessionContext]:
    return _sessions.get(session_id)


def get_or_create_session(
    session_id: str,
    customer_id: Optional[str] = None,
    language: str = "en",
) -> SessionContext:

    existing_session = get_session(session_id)

    if existing_session:
        return existing_session

    return create_session(
        session_id=session_id,
        customer_id=customer_id,
        language=language,
    )


def remove_session(session_id: str) -> bool:
    if session_id in _sessions:
        del _sessions[session_id]
        return True

    return False