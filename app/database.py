from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime
from datetime import datetime
from typing import AsyncGenerator

from app.config import settings


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


async def init_db() -> None:
    """Initialize database tables."""
    from sqlalchemy.exc import ProgrammingError, OperationalError

    try:
        async with engine.begin() as conn:
            # checkfirst=True prevents errors if tables already exist
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    except (ProgrammingError, OperationalError) as e:
        # Handle cases where indexes/constraints already exist
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            print(f"Database objects already exist, continuing: {e}")
        else:
            raise
    except Exception as e:
        # Log but don't fail startup if tables already exist
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            print(f"Database initialization warning (non-fatal): {e}")
        else:
            raise
