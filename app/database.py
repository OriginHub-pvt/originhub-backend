"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
from dotenv import load_dotenv
import logging

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('POSTGRES_USER', 'originhub')}:{os.getenv('POSTGRES_PASSWORD', 'originhub123')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'originhub')}",
)

# Create SQLAlchemy engine with connection pooling and retry logic
# pool_pre_ping=True: Tests connections before using them (handles stale connections)
# pool_recycle=3600: Recycle connections after 1 hour
# pool_size=5: Number of connections to maintain
# max_overflow=10: Additional connections that can be created
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,  # Base pool size
    max_overflow=10,  # Max overflow connections
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Set up logging
logger = logging.getLogger(__name__)


def get_db():
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.

    Handles connection errors gracefully and retries if needed.
    """
    db = SessionLocal()
    try:
        yield db
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Database connection error: {e}")
        db.rollback()
        # Try to reconnect
        try:
            db.close()
            db = SessionLocal()
            yield db
        except Exception as retry_error:
            logger.error(f"Failed to reconnect to database: {retry_error}")
            raise
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
