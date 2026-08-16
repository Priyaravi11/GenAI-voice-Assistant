import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# DATABASE
# ============================================================

from backend.app.database import network_collection


# ============================================================
# HELPER FUNCTION
# ============================================================

def _find_network_by_area(area: str):
    """
    Find a network record from the nested network array
    using a case-insensitive area match.
    """

    document = network_collection.find_one(
        {
            "network": {
                "$elemMatch": {
                    "area": {
                        "$regex": f"^{area}$",
                        "$options": "i"
                    }
                }
            }
        },
        {
            "_id": 0,
            "network": 1
        }
    )

    if document is None:
        return None

    for network in document.get("network", []):

        network_area = network.get("area", "")

        if network_area.lower() == area.lower():
            return network

    return None


# ============================================================
# NETWORK TOOL 1
# Get Network Status
# ============================================================

def get_network_status(area: str):
    """
    Get the current network status for an area.
    """

    try:

        network = _find_network_by_area(area)

        if network is None:

            return {
                "success": False,
                "area": area,
                "message": f"No network information found for area {area}"
            }

        return {
            "success": True,
            "area": area,
            "message": "Network status retrieved successfully",
            "data": {
                "area": network.get("area"),
                "status": network.get("status")
            }
        }

    except Exception as e:

        return {
            "success": False,
            "area": area,
            "message": "Failed to retrieve network status",
            "error": str(e)
        }


# ============================================================
# NETWORK TOOL 2
# Get Network Issue
# ============================================================

def get_network_issue(area: str):
    """
    Get the network issue reported for an area.
    """

    try:

        network = _find_network_by_area(area)

        if network is None:

            return {
                "success": False,
                "area": area,
                "message": f"No network information found for area {area}"
            }

        issue = network.get("issue")

        if not issue:

            return {
                "success": True,
                "area": area,
                "message": "No network issue reported for this area",
                "data": {
                    "area": network.get("area"),
                    "issue": None
                }
            }

        return {
            "success": True,
            "area": area,
            "message": "Network issue retrieved successfully",
            "data": {
                "area": network.get("area"),
                "issue": issue
            }
        }

    except Exception as e:

        return {
            "success": False,
            "area": area,
            "message": "Failed to retrieve network issue",
            "error": str(e)
        }


# ============================================================
# NETWORK TOOL 3
# Get Resolution Time
# ============================================================

def get_resolution_time(area: str):
    """
    Get the estimated resolution time for a network issue.
    """

    try:

        network = _find_network_by_area(area)

        if network is None:

            return {
                "success": False,
                "area": area,
                "message": f"No network information found for area {area}"
            }

        resolution_time = network.get("estimated_resolution")

        if not resolution_time:

            return {
                "success": False,
                "area": area,
                "message": "No estimated resolution time is available for this area"
            }

        return {
            "success": True,
            "area": area,
            "message": "Estimated resolution time retrieved successfully",
            "data": {
                "area": network.get("area"),
                "estimated_resolution": resolution_time
            }
        }

    except Exception as e:

        return {
            "success": False,
            "area": area,
            "message": "Failed to retrieve resolution time",
            "error": str(e)
        }


# ============================================================
# NETWORK TOOL 4
# Check Area Service
# ============================================================

def check_area_service(area: str):
    """
    Check whether network service is available in an area.
    """

    try:

        network = _find_network_by_area(area)

        if network is None:

            return {
                "success": False,
                "area": area,
                "message": f"No network information found for area {area}"
            }

        status = network.get("status")

        if status == "operational":

            service_available = True
            service_message = "Network service is available"

        elif status in ["down", "outage"]:

            service_available = False
            service_message = "Network service is currently unavailable"

        elif status == "degraded":

            service_available = True
            service_message = "Network service is available but degraded"

        elif status == "maintenance":

            service_available = False
            service_message = (
                "Network service is temporarily affected by maintenance"
            )

        else:

            service_available = False
            service_message = "Network service status is unknown"

        return {
            "success": True,
            "area": area,
            "message": service_message,
            "data": {
                "area": network.get("area"),
                "status": status,
                "service_available": service_available
            }
        }

    except Exception as e:

        return {
            "success": False,
            "area": area,
            "message": "Failed to check area service",
            "error": str(e)
        }


# ============================================================
# NETWORK TOOL 5
# Get Network Details
# ============================================================

def get_network_details(area: str):
    """
    Get complete network details for an area.
    """

    try:

        network = _find_network_by_area(area)

        if network is None:

            return {
                "success": False,
                "area": area,
                "message": f"No network information found for area {area}"
            }

        return {
            "success": True,
            "area": area,
            "message": "Network details retrieved successfully",
            "data": {
                "area": network.get("area"),
                "status": network.get("status"),
                "issue": network.get("issue"),
                "estimated_resolution": network.get(
                    "estimated_resolution"
                )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "area": area,
            "message": "Failed to retrieve network details",
            "error": str(e)
        }