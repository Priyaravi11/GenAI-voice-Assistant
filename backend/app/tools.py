# ============================================================
# TOOL REGISTRY / TOOL EXECUTOR
# File: backend/app/tools.py
#
# Purpose:
# Central entry point for all telecom database tools.
#
# Individual tool implementations are located in:
#
# tools/
# ├── billing_tool.py
# ├── customer_tool.py
# ├── network_tool.py
# ├── payment_tool.py
# └── plans_tool.py
#
# Agents should call tools through this file instead of
# directly depending on individual tool modules.
# ============================================================


import inspect
from typing import Any, Dict

import logging
import traceback


# ============================================================
# IMPORT TOOL MODULES
# ============================================================

from tools import billing_tool
from tools import customer_tool
from tools import network_tool
from tools import payment_tool
from tools import plans_tool


# ============================================================
# TOOL MODULES
# ============================================================

TOOL_MODULES = {
    "billing": billing_tool,
    "customer": customer_tool,
    "network": network_tool,
    "payment": payment_tool,
    "plans": plans_tool,
}


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {}


# ============================================================
# REGISTER FUNCTIONS FROM TOOL MODULES
# ============================================================

def _register_tools():
    """
    Automatically register all public tool functions
    from the individual tool modules.

    Only functions defined inside the individual tool modules
    are registered.

    Functions beginning with '_' are ignored.
    """

    for module_name, module in TOOL_MODULES.items():

        for function_name, function in inspect.getmembers(
            module,
            inspect.isfunction
        ):

            # Ignore private/helper functions
            if function_name.startswith("_"):
                continue

            # Make sure the function actually belongs
            # to this module.
            if function.__module__ != module.__name__:
                continue

            # Register function
            TOOL_REGISTRY[function_name] = function


# Register all tools when this file is imported
_register_tools()


# ============================================================
# GET TOOL
# ============================================================

def get_tool(tool_name: str):
    """
    Get a tool function from the tool registry.

    Example:

        tool = get_tool("get_customer_autopay")
    """

    return TOOL_REGISTRY.get(tool_name)


# ============================================================
# CHECK WHETHER TOOL EXISTS
# ============================================================

def tool_exists(tool_name: str) -> bool:
    """
    Check whether a tool is registered.
    """

    return tool_name in TOOL_REGISTRY


# ============================================================
# LIST ALL AVAILABLE TOOLS
# ============================================================

def list_tools():
    """
    Return the names of all registered tools.
    """

    return sorted(TOOL_REGISTRY.keys())


# ============================================================
# GET TOOL INFORMATION
# ============================================================

def get_tool_info(tool_name: str):
    """
    Return basic information about a registered tool.
    """

    tool = get_tool(tool_name)

    if tool is None:

        return {
            "success": False,
            "tool": tool_name,
            "message": f"Tool '{tool_name}' is not registered"
        }

    return {
        "success": True,
        "tool": tool_name,
        "module": tool.__module__,
        "description": inspect.getdoc(tool)
    }


# ============================================================
# EXECUTE TOOL
# ============================================================


logger = logging.getLogger(__name__)

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:

    tool_function = get_tool(tool_name)

    if tool_function is None:
        return {
            "success": False,
            "tool": tool_name,
            "message": f"Tool '{tool_name}' is not registered",
            "available_tools": list_tools()
        }

    try:
        logger.info(
            "Executing tool: %s | kwargs=%s",
            tool_name,
            kwargs
        )

        result = tool_function(**kwargs)

        if inspect.isawaitable(result):
            return {
                "success": False,
                "tool": tool_name,
                "message": (
                    f"Tool '{tool_name}' is asynchronous. "
                    "Use execute_tool_async() instead."
                )
            }

        logger.info(
            "Tool completed: %s | result=%s",
            tool_name,
            result
        )

        return result

    except Exception as e:

        logger.exception(
            "TOOL EXECUTION FAILED: %s | kwargs=%s",
            tool_name,
            kwargs
        )

        return {
            "success": False,
            "tool": tool_name,
            "message": f"Failed to execute tool '{tool_name}'",
            "error": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
    """
    Execute a registered telecom tool.

    Parameters
    ----------
    tool_name : str
        Name of the tool to execute.

    kwargs
        Arguments required by the selected tool.

    Example
    -------
        result = execute_tool(
            "get_customer_autopay",
            cust_id="C129"
        )
    """

    # --------------------------------------------------------
    # Check whether tool exists
    # --------------------------------------------------------

    tool_function = get_tool(tool_name)

    if tool_function is None:

        return {
            "success": False,
            "tool": tool_name,
            "message": f"Tool '{tool_name}' is not registered",
            "available_tools": list_tools()
        }

    # --------------------------------------------------------
    # Execute tool
    # --------------------------------------------------------

    try:

        result = tool_function(**kwargs)

        # ----------------------------------------------------
        # Handle accidental async functions
        # ----------------------------------------------------

        if inspect.isawaitable(result):

            return {
                "success": False,
                "tool": tool_name,
                "message": (
                    f"Tool '{tool_name}' is asynchronous. "
                    "Use execute_tool_async() instead."
                )
            }

        # ----------------------------------------------------
        # Return original tool result
        # ----------------------------------------------------

        return result

    except TypeError as e:

        return {
            "success": False,
            "tool": tool_name,
            "message": (
                f"Invalid arguments provided for tool "
                f"'{tool_name}'"
            ),
            "error": str(e)
        }

    except Exception as e:

        return {
            "success": False,
            "tool": tool_name,
            "message": (
                f"Failed to execute tool '{tool_name}'"
            ),
            "error": str(e)
        }


# ============================================================
# ASYNC TOOL EXECUTION
# ============================================================

# async def execute_tool_async(
#     tool_name: str,
#     **kwargs
# ) -> Dict[str, Any]:
#     """
#     Execute both synchronous and asynchronous tools.

#     This function is useful when the FastAPI/Agent layer
#     becomes asynchronous.
#     """

#     # --------------------------------------------------------
#     # Get tool
#     # --------------------------------------------------------

#     tool_function = get_tool(tool_name)

#     if tool_function is None:

#         return {
#             "success": False,
#             "tool": tool_name,
#             "message": f"Tool '{tool_name}' is not registered",
#             "available_tools": list_tools()
#         }

#     # --------------------------------------------------------
#     # Execute
#     # --------------------------------------------------------

#     try:

#         result = tool_function(**kwargs)

#         # ----------------------------------------------------
#         # Wait for async result if required
#         # ----------------------------------------------------

#         if inspect.isawaitable(result):
#             result = await result

#         return result

#     except TypeError as e:

#         return {
#             "success": False,
#             "tool": tool_name,
#             "message": (
#                 f"Invalid arguments provided for tool "
#                 f"'{tool_name}'"
#             ),
#             "error": str(e)
#         }

#     except Exception as e:

#         return {
#             "success": False,
#             "tool": tool_name,
#             "message": (
#                 f"Failed to execute tool '{tool_name}'"
#             ),
#             "error": str(e)
#         }


# ============================================================
# GROUP TOOLS BY MODULE
# ============================================================

def get_tools_by_category():
    """
    Return all registered tools grouped according to
    their tool module.
    """

    categories = {}

    for category, module in TOOL_MODULES.items():

        categories[category] = []

        for tool_name, tool_function in TOOL_REGISTRY.items():

            if tool_function.__module__ == module.__name__:

                categories[category].append(tool_name)

        categories[category].sort()

    return categories


# ============================================================
# TOOL REGISTRY SUMMARY
# ============================================================

def get_tool_summary():
    """
    Return a summary of the complete tool registry.
    """

    categories = get_tools_by_category()

    return {
        "total_tools": len(TOOL_REGISTRY),
        "categories": categories,
        "tools": list_tools()
    }


# ============================================================
# TEMPORARY TEST CODE
# Delete or keep for development testing
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("             TELECOM TOOL REGISTRY")
    print("=" * 60)

    # --------------------------------------------------------
    # Display total number of tools
    # --------------------------------------------------------

    print("\nTotal registered tools:")
    print(len(TOOL_REGISTRY))

    # --------------------------------------------------------
    # Display tools category-wise
    # --------------------------------------------------------

    print("\n========== TOOLS BY CATEGORY ==========")

    categories = get_tools_by_category()

    for category, tools in categories.items():

        print(f"\n[{category.upper()}]")

        if tools:

            for tool_name in tools:
                print("  -", tool_name)

        else:

            print("  No tools registered")

    # --------------------------------------------------------
    # Display all tools
    # --------------------------------------------------------

    print("\n========== ALL AVAILABLE TOOLS ==========")

    for tool_name in list_tools():
        print("-", tool_name)

    # --------------------------------------------------------
    # Test customer autopay
    # --------------------------------------------------------

    if "get_customer_autopay" in TOOL_REGISTRY:

        print("\n")
        print("=" * 60)
        print("       TESTING CUSTOMER AUTOPAY TOOL")
        print("=" * 60)

        customer_id = "C129"

        print("\nCustomer ID:", customer_id)

        result = execute_tool(
            "get_customer_autopay",
            cust_id=customer_id
        )

        print("\nResult:")
        print(result)

    else:

        print("\nCustomer autopay tool was not found.")

    print("\n")
    print("=" * 60)
    print("                 TEST COMPLETE")
    print("=" * 60)