"""
Tool Routes
File: backend/app/routes/tools.py

Provides FastAPI endpoints for accessing the registered
telecom tools.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from bac.app.tools import get_tool, list_tools


router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


# ============================================================
# LIST AVAILABLE TOOLS
# ============================================================

@router.get("/")
async def get_available_tools():
    """
    Return the list of all available telecom tools.
    """

    return {
        "success": True,
        "tools": list_tools(),
    }


# ============================================================
# EXECUTE TOOL
# ============================================================

@router.post("/execute")
async def execute_tool(request: ToolRequest):
    """
    Execute a registered telecom tool.

    Example:

    {
        "tool_name": "get_current_bill",
        "parameters": {
            "cust_id": "C251"
        }
    }
    """

    try:

        tool = get_tool(request.tool_name)

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    try:

        result = tool(**request.parameters)

        return {
            "success": True,
            "tool_name": request.tool_name,
            "result": result,
        }

    except TypeError as e:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid tool parameters: {str(e)}",
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}",
        )