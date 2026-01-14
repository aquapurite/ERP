"""
Base utilities for SQLAlchemy models.

IMPORTANT: This project uses String(36) for all UUID columns instead of UUID(as_uuid=True).

Why? PostgreSQL has strict type casting. When using UUID columns with SQLAlchemy:
- If the database column is VARCHAR, SQLAlchemy's UUID type adds ::UUID casts
- This causes "operator does not exist: character varying = uuid" errors

Solution: Use String(36) for all ID columns. This:
- Works with both UUID and VARCHAR database columns
- Avoids type casting issues
- Is compatible with existing data

Usage:
    from app.models.base import StringUUID, generate_uuid

    class MyModel(Base):
        __tablename__ = "my_table"
        id = Column(StringUUID, primary_key=True, default=generate_uuid)
        parent_id = Column(StringUUID, ForeignKey("parents.id"))
"""

import uuid
from sqlalchemy import String

# Standard UUID column type - always use this instead of UUID(as_uuid=True)
StringUUID = String(36)


def generate_uuid() -> str:
    """Generate a UUID string for use as primary key."""
    return str(uuid.uuid4())


# For backward compatibility and explicit imports
__all__ = ['StringUUID', 'generate_uuid']
