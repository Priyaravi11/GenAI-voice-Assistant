from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.orchestrator import orchestrator
from backend.app.validation import (
    validate_customer_id,
    validate_customer_query,
    validate_language,
    validate_session_id,
)


router = APIRouter(
    prefix="/calls",
    tags=["Calls"],
)


class CallRequest(BaseModel):
    session_id: str
    customer_query: str
    language: str = "en"
    customer_id: Optional[str] = None
    nlu_data: Optional[Dict[str, Any]] = Field(default=None)


@router.post("/process")
async def process_call(request: CallRequest):
    """
    Process a customer request through the orchestrator.
    """

    try:
        session_id = validate_session_id(request.session_id)
        customer_query = validate_customer_query(request.customer_query)
        language = validate_language(request.language)
        customer_id = validate_customer_id(request.customer_id)

        result = await orchestrator.process_text(
            session_id=session_id,
            customer_query=customer_query,
            language=language,
            customer_id=customer_id,
            nlu_data=request.nlu_data,
        )

        return {
            "success": True,
            "data": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Call processing failed.",
        ) from exc