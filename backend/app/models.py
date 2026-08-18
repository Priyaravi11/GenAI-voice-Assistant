from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# -------------------------
# Session Models
# -------------------------

class SessionCreate(BaseModel):
    language: str = "en"
    customer_id: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    language: str
    customer_id: Optional[str] = None
    status: str = "active"


class LoginRequest(BaseModel):
    cust_id: str
    account_id: str


class LoginResponse(SessionResponse):
    account_id: str
    account_status: Optional[str] = None
    connection_status: Optional[str] = None


# -------------------------
# Call Models
# -------------------------

class CallStartRequest(BaseModel):
    session_id: str
    customer_id: Optional[str] = None
    language: str = "en"


class CallEndRequest(BaseModel):
    session_id: str
    reason: Optional[str] = None


class CallResponse(BaseModel):
    call_id: str
    session_id: str
    status: str


# -------------------------
# NLU / RAG Models
# -------------------------

class LanguageInfo(BaseModel):
    primary: str = "en"
    code_switched: bool = False


class IntentInfo(BaseModel):
    name: str


class SentimentInfo(BaseModel):
    label: str = "neutral"


class RAGQueryRequest(BaseModel):
    request_id: str
    language: LanguageInfo = Field(default_factory=LanguageInfo)
    intent: IntentInfo
    entities: Dict[str, Any] = Field(default_factory=dict)
    sentiment: Optional[SentimentInfo] = None
    customer_query: str


class RAGQueryResponse(BaseModel):
    success: bool
    data: Any


# -------------------------
# Tool Models
# -------------------------

class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolResponse(BaseModel):
    success: bool
    tool_name: str
    result: Any = None
    error: Optional[str] = None


# -------------------------
# WebSocket Models
# -------------------------

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class WebSocketResponse(BaseModel):
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


# -------------------------
# Generic API Response
# -------------------------

class APIResponse(BaseModel):
    success: bool
    message: str = ""
    data: Any = None
