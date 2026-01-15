"""
NeurOS 2.0 Database Configuration

Async SQLAlchemy 2.0 setup with PostgreSQL or SQLite.
Provides session management and base model.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, StaticPool

from app.config import settings


# Determine engine kwargs based on database type
db_url = settings.async_database_url
is_sqlite = "sqlite" in db_url

if is_sqlite:
    # SQLite config - use StaticPool for async sqlite
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
else:
    # PostgreSQL config
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "poolclass": NullPool if settings.ENVIRONMENT == "testing" else None,
    }

# Create async engine
engine = create_async_engine(db_url, **engine_kwargs)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
