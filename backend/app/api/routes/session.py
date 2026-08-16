from fastapi import APIRouter, HTTPException

from app.context import (
    create_session,
    get_session,
    remove_session,
)
from app.models import SessionCreate, SessionResponse
from app.validation import (
    validate_customer_id,
    validate_language,
    validate_session_id,
)

router = APIRouter(
    prefix="/session",
    tags=["Session"],
)


@router.post("", response_model=SessionResponse)
async def create_new_session(request: SessionCreate):
    """
    Create a new customer session.
    """

    try:
        language = validate_language(request.language)
        customer_id = validate_customer_id(request.customer_id)

        # Generate a simple unique session ID
        import uuid

        session_id = str(uuid.uuid4())

        context = create_session(
            session_id=session_id,
            customer_id=customer_id,
            language=language,
        )

        return SessionResponse(
            session_id=context.session_id,
            language=context.language,
            customer_id=context.customer_id,
            status=context.status,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(session_id: str):
    """
    Get the details of an active session.
    """

    try:
        session_id = validate_session_id(session_id)

        context = get_session(session_id)

        if context is None:
            raise HTTPException(
                status_code=404,
                detail="Session not found.",
            )

        return SessionResponse(
            session_id=context.session_id,
            language=context.language,
            customer_id=context.customer_id,
            status=context.status,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{session_id}")
async def close_session(session_id: str):
    """
    Close and remove a session.
    """

    try:
        session_id = validate_session_id(session_id)

        context = get_session(session_id)

        if context is None:
            raise HTTPException(
                status_code=404,
                detail="Session not found.",
            )

        context.close()
        remove_session(session_id)

        return {
            "success": True,
            "message": "Session closed successfully.",
            "session_id": session_id,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )