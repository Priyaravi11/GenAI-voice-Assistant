import re
from typing import Optional


SUPPORTED_LANGUAGES = {
    "en",
    "hi",
    "ta",
    "te",
    "kn",
    "ml",
    "bn",
    "mr",
    "gu",
    "pa",
}


def validate_session_id(session_id: str) -> str:
    """
    Validate a session ID.
    """
    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    session_id = session_id.strip()

    if len(session_id) > 100:
        raise ValueError("Session ID is too long.")

    if not re.match(r"^[A-Za-z0-9_-]+$", session_id):
        raise ValueError("Session ID contains invalid characters.")

    return session_id


def validate_customer_id(customer_id: Optional[str]) -> Optional[str]:
    """
    Validate an optional customer ID.
    """
    if customer_id is None:
        return None

    customer_id = customer_id.strip()

    if not customer_id:
        raise ValueError("Customer ID cannot be empty.")

    if len(customer_id) > 100:
        raise ValueError("Customer ID is too long.")

    return customer_id


def validate_language(language: str) -> str:
    """
    Validate a language code.
    """
    if not language or not language.strip():
        raise ValueError("Language cannot be empty.")

    language = language.strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}"
        )

    return language


def validate_customer_query(query: str) -> str:
    """
    Validate a customer query before sending it
    to downstream processing such as RAG.
    """
    if not query or not query.strip():
        raise ValueError("Customer query cannot be empty.")

    query = query.strip()

    if len(query) > 5000:
        raise ValueError("Customer query is too long.")

    return query


def validate_tool_name(tool_name: str) -> str:
    """
    Validate a requested tool name.
    """
    if not tool_name or not tool_name.strip():
        raise ValueError("Tool name cannot be empty.")

    return tool_name.strip()


def validate_request_id(request_id: str) -> str:
    """
    Validate a request ID.
    """
    if not request_id or not request_id.strip():
        raise ValueError("Request ID cannot be empty.")

    return request_id.strip()