import json
from decimal import Decimal
from datetime import datetime, date
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime, event
from sqlalchemy.dialects.postgresql import JSONB
import psycopg
from psycopg.types.json import set_json_dumps, set_json_loads

from app.config import settings


# Custom JSON encoder that handles Decimal, datetime, UUID, etc.
class CustomJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal, datetime, UUID and other types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def custom_json_dumps(obj):
    """Custom JSON dumps function for psycopg."""
    return json.dumps(obj, cls=CustomJSONEncoder)


# Configure psycopg to use our custom JSON encoder globally
set_json_dumps(custom_json_dumps)


# SQLite doesn't support pool settings, check database type
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Convert database URL for proper driver
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg://"):
    # Switch to psycopg for async PostgreSQL
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://")

# Create async engine with appropriate settings
if is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={
            "prepare_threshold": None,  # Disable prepared statements to avoid DuplicatePreparedStatement errors
        },
    )

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class TimestampMixin:
    """Mixin for adding created_at and updated_at columns."""
    pass  # Timestamps are defined in each model directly


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Context manager for getting database session (for background jobs)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables."""
    # Import all models to register them with Base.metadata
    from app import models  # noqa: F401

    print(f"Registered {len(Base.metadata.tables)} tables")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")
    except Exception as e:
        # Ignore "already exists" errors
        if "already exists" in str(e).lower():
            print("Database tables already exist")
        else:
            print(f"Database warning: {e}")
