"""
Database Configuration and Session Management
Handles PostgreSQL connection, session lifecycle, and dependency injection for FastAPI.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variable (REQUIRED)
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate DATABASE_URL is set
if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL environment variable is required.\n"
        "Please create a .env file in the project root with:\n"
        "DATABASE_URL=postgresql://user:password@host:port/database\n\n"
        "See DATABASE_SETUP.md for detailed setup instructions."
    )

# Create SQLAlchemy engine
# pool_pre_ping ensures connections are alive before using them
# echo=True for development (set to False in production)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI routes.
    Provides a database session and ensures proper cleanup.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    from backend.db_models import Base as DBBase  # Import to register models
    
    try:
        # Create all tables
        DBBase.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        raise


def test_connection() -> bool:
    """
    Test database connection.
    Returns True if connection is successful, False otherwise.
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# Connection pooling events for debugging (optional)
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections (development only)"""
    if os.getenv("SQL_DEBUG", "false").lower() == "true":
        print("🔌 New database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log database connection closures (development only)"""
    if os.getenv("SQL_DEBUG", "false").lower() == "true":
        print("🔌 Database connection closed")
