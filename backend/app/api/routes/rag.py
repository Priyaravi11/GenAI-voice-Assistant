from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


class LanguageInput(BaseModel):
    primary: str = "en"
    code_switched: bool = False


class IntentInput(BaseModel):
    name: str


class SentimentInput(BaseModel):
    label: str = "neutral"


class RAGQueryRequest(BaseModel):
    request_id: str
    language: LanguageInput = Field(default_factory=LanguageInput)
    intent: IntentInput
    entities: Dict[str, Any] = Field(default_factory=dict)
    sentiment: Optional[SentimentInput] = None
    customer_query: str


@router.post("/query")
async def query_rag(request: RAGQueryRequest):
    """
    Send NLU output to the RAG service and return
    the retrieved context.
    """

    try:
        from backend.app.rag import retrieve_context

        nlu_data = request.model_dump()

        result = retrieve_context(nlu_data)

        return {
            "success": True,
            "data": result,
        }

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="RAG retrieval failed.",
        ) from exc
