"""
Enum Utilities for VARCHAR-based Status Fields

ARCHITECTURE STANDARD (from CLAUDE.md):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Database: VARCHAR(50) - NOT PostgreSQL ENUM
• SQLAlchemy: String(50) with Mapped[str]
• Pydantic: Python Enum for API validation
• API Response: Use string directly (NO .value needed)

DATA FLOW:
━━━━━━━━━━
INPUT (API Request):
    Pydantic Enum → .value → String → Database
    Example: OrderStatus.PENDING → "PENDING" → VARCHAR

OUTPUT (API Response):
    Database → String → Return directly
    Example: VARCHAR "PENDING" → "PENDING" (no conversion needed)

USAGE PATTERNS:
━━━━━━━━━━━━━━━
1. In SQLAlchemy Models:
   status: Mapped[str] = mapped_column(String(50), default="PENDING")

2. In Pydantic Schemas (for INPUT validation):
   status: OrderStatus = OrderStatus.PENDING

3. In API Responses (reading from DB):
   return {"status": order.status}  # Already a string, use directly

4. In API Responses (with enum input):
   return {"status": get_enum_value(data.status)}  # Safe for both
"""

from enum import Enum
from typing import Any, Optional, TypeVar, Type


T = TypeVar('T', bound=Enum)


def get_enum_value(value: Any) -> str:
    """
    Safely get string value from an enum or string.

    Use this when you're unsure if the value is:
    - A Pydantic enum (from input) - has .value
    - A database string (from query) - is already a string

    Args:
        value: Either an Enum instance or a string

    Returns:
        The string value

    Examples:
        >>> get_enum_value(OrderStatus.PENDING)  # Pydantic input
        'PENDING'
        >>> get_enum_value("PENDING")  # Database value
        'PENDING'
        >>> get_enum_value(None)
        None
    """
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    return str(value)


def get_enum_name(value: Any) -> str:
    """
    Safely get name from an enum or string.

    Args:
        value: Either an Enum instance or a string

    Returns:
        The name (for enums) or the string itself
    """
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.name
    return str(value)


def to_enum(value: Any, enum_class: Type[T]) -> Optional[T]:
    """
    Convert a string value to an enum instance.

    Use this when you need to convert a database string
    back to an enum for comparison or validation.

    Args:
        value: String value from database
        enum_class: The Enum class to convert to

    Returns:
        Enum instance or None if not found

    Examples:
        >>> to_enum("PENDING", OrderStatus)
        OrderStatus.PENDING
        >>> to_enum("INVALID", OrderStatus)
        None
    """
    if value is None:
        return None
    if isinstance(value, enum_class):
        return value
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return None


def enum_values(enum_class: Type[Enum]) -> list:
    """
    Get all values from an enum class.

    Useful for generating comment strings for VARCHAR columns.

    Args:
        enum_class: The Enum class

    Returns:
        List of all enum values

    Examples:
        >>> enum_values(OrderStatus)
        ['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED']
    """
    return [e.value for e in enum_class]


def enum_comment(enum_class: Type[Enum]) -> str:
    """
    Generate a comment string for VARCHAR column.

    Use this in SQLAlchemy model column definitions.

    Args:
        enum_class: The Enum class

    Returns:
        Comma-separated string of valid values

    Examples:
        >>> enum_comment(OrderStatus)
        'PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED'
    """
    return ", ".join(enum_values(enum_class))


# =============================================================================
# COMPARISON HELPERS
# =============================================================================

def is_status(db_value: str, enum_value: Enum) -> bool:
    """
    Compare a database string with an enum value.

    Args:
        db_value: String from database
        enum_value: Enum to compare with

    Returns:
        True if they match

    Examples:
        >>> is_status(order.status, OrderStatus.PENDING)
        True
    """
    if db_value is None:
        return False
    return db_value == enum_value.value


def status_in(db_value: str, *enum_values: Enum) -> bool:
    """
    Check if database value matches any of the given enums.

    Args:
        db_value: String from database
        enum_values: Enum values to check against

    Returns:
        True if db_value matches any enum value

    Examples:
        >>> status_in(order.status, OrderStatus.PENDING, OrderStatus.CONFIRMED)
        True
    """
    if db_value is None:
        return False
    return db_value in [e.value for e in enum_values]


# =============================================================================
# LEVEL COMPARISON (for Role hierarchy)
# =============================================================================

def compare_levels(level1: str, level2: str, level_order: dict) -> int:
    """
    Compare two level strings using a hierarchy order.

    Args:
        level1: First level string
        level2: Second level string
        level_order: Dict mapping level names to numeric values

    Returns:
        -1 if level1 < level2 (higher authority)
         0 if equal
         1 if level1 > level2 (lower authority)
    """
    val1 = level_order.get(level1, 999)
    val2 = level_order.get(level2, 999)

    if val1 < val2:
        return -1
    elif val1 > val2:
        return 1
    return 0
