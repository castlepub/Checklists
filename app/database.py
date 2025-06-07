from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import asyncio
from sqlalchemy import text
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in Railway's environment variables or in .env file."
    )

# Convert postgres:// to postgresql:// for compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure SQLAlchemy engine with longer timeout and connection retry settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 60  # Allow up to 60 seconds for connection
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def test_db_connection():
    """Test database connection without creating tables."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Testing database connection (attempt {attempt + 1}/{max_retries})")
            # Use a connection from the pool
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before next attempt...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("All database connection attempts failed")
                return False

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 