"""
Database connection and session management.

WHY: Centralizing database setup enables:
- Clean dependency injection in routes
- Consistent session handling
- Easy migration to other databases later
- Proper connection pooling and cleanup
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from config import settings

# WHY: SQLite-specific settings for single-file database
# StaticPool for SQLite to handle multi-threading safely
# check_same_thread=False required for FastAPI async context
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.DEBUG  # Log SQL in debug mode
)

# WHY: Enable foreign key constraints in SQLite (disabled by default)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
# WHY: autocommit=False, autoflush=False for explicit transaction control
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency that provides database session.
    
    WHY: Generator pattern ensures proper cleanup even on exceptions.
    Used as FastAPI dependency injection for all routes needing DB access.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    
    WHY: Separate from engine creation to allow:
    - Importing models before table creation
    - Testing with fresh databases
    - Future migration system integration
    """
    # Import models to register them with Base
    from models import entry, pattern, reflection, analytics, recommendation, learning_plan
    
    Base.metadata.create_all(bind=engine)
