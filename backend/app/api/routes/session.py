from fastapi import APIRouter, HTTPException

from backend.app.context import (
    create_session,
    get_session,
    remove_session,
)
from backend.app.database import accounts_collection
from backend.app.models import LoginRequest, LoginResponse, SessionCreate, SessionResponse
from backend.app.validation import (
    validate_customer_id,
    validate_session_id,
)

router = APIRouter(
    prefix="/session",
    tags=["Session"],
)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Validate a customer account and create an active session.
    """

    try:
        customer_id = validate_customer_id(request.cust_id)
        account_id = request.account_id.strip()

        if not account_id:
            raise ValueError("Account ID cannot be empty.")

        account_document = accounts_collection.find_one(
            {
                "accounts": {
                    "$elemMatch": {
                        "cust_id": customer_id,
                        "account_id": account_id,
                    }
                }
            },
            {"accounts.$": 1},
        )

        if not account_document or not account_document.get("accounts"):
            raise HTTPException(
                status_code=401,
                detail="Invalid customer ID or account ID.",
            )

        account = account_document["accounts"][0]

        if account.get("account_status") != "active":
            raise HTTPException(
                status_code=403,
                detail="Account is not active.",
            )

        import uuid

        context = create_session(
            session_id=str(uuid.uuid4()),
            customer_id=customer_id,
            language="en",
        )

        context.update(
            account_id=account_id,
            account_type=account.get("account_type"),
            connection_status=account.get("connection_status"),
        )

        return LoginResponse(
            session_id=context.session_id,
            language=context.language,
            customer_id=context.customer_id,
            status=context.status,
            account_id=account_id,
            account_status=account.get("account_status"),
            connection_status=account.get("connection_status"),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("", response_model=SessionResponse)
async def create_new_session(request: SessionCreate):
    """
    Create a new customer session.
    """

    try:
        from backend.app.validation import validate_language

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
