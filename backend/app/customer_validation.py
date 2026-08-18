"""
Customer Validation

Provides validation functions for customer-related data,
particularly customer IDs.

Used by the orchestrator and agents to ensure that
customer IDs are valid before executing tools.
"""

from typing import Optional, Tuple


def validate_customer_id(
    customer_id: Optional[str],
    allow_none: bool = False,
) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a customer ID.

    Args:
        customer_id:
            The customer ID to validate.
        allow_none:
            If True, None/empty IDs are considered valid.
            If False, they are considered invalid.

    Returns:
        Tuple of (is_valid, error_message, normalized_id)

        is_valid:
            True if the ID is valid, False otherwise.
        error_message:
            Human-readable error message if invalid, empty string if valid.
        normalized_id:
            Cleaned/normalized customer ID if valid, None otherwise.

    Examples:

        >>> validate_customer_id("C251")
        (True, "", "C251")

        >>> validate_customer_id("  C251  ")
        (True, "", "C251")

        >>> validate_customer_id("")
        (False, "Customer ID cannot be empty.", None)

        >>> validate_customer_id(None, allow_none=True)
        (True, "", None)

        >>> validate_customer_id(None, allow_none=False)
        (False, "Customer ID is required.", None)
    """

    # ================================================================
    # Handle None / Empty
    # ================================================================

    if customer_id is None:

        if allow_none:
            return (True, "", None)

        return (False, "Customer ID is required.", None)

    # ================================================================
    # Type Check
    # ================================================================

    if not isinstance(customer_id, str):

        return (False, "Customer ID must be a string.", None)

    # ================================================================
    # Normalize
    # ================================================================

    normalized = customer_id.strip()

    # ================================================================
    # Empty Check
    # ================================================================

    if not normalized:

        if allow_none:
            return (True, "", None)

        return (False, "Customer ID cannot be empty.", None)

    # ================================================================
    # Format Check
    # ================================================================
    # The customer ID is expected to start with 'C' followed by digits.
    # Example: "C251", "C1000", etc.
    #
    # However, we're lenient here to allow for future variations.
    # The minimum requirement is that it's not empty and has content.
    # ================================================================

    # Check for obviously invalid characters
    if not _is_valid_customer_id_format(normalized):

        return (
            False,
            "Customer ID contains invalid characters. "
            "Please provide a valid customer ID.",
            None,
        )

    # ================================================================
    # Valid
    # ================================================================

    return (True, "", normalized)


def _is_valid_customer_id_format(
    customer_id: str,
) -> bool:
    """
    Check whether a customer ID has a valid format.

    A valid customer ID should:
    - Not be empty (already checked before calling this)
    - Contain only alphanumeric characters, dashes, and underscores
    - Not contain spaces or special characters
    """

    # Allow alphanumeric, dash, underscore
    for char in customer_id:
        if not (char.isalnum() or char in "-_"):
            return False

    return True


def is_customer_id_valid(
    customer_id: Optional[str],
) -> bool:
    """
    Quick validation check for customer IDs.

    Returns True if the ID is valid, False otherwise.

    Usage:

        if is_customer_id_valid(customer_id):
            # Safe to use
        else:
            # Ask customer for ID again
    """

    is_valid, _, _ = validate_customer_id(
        customer_id,
        allow_none=False,
    )

    return is_valid
