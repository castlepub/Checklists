from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import asyncio
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add file handler for persistent logs
file_handler = logging.FileHandler('database.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
logger.info(f"Database URL format: {'postgresql' in DATABASE_URL if DATABASE_URL else 'None'}")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")

# Create SQLAlchemy engine with detailed logging
try:
    logger.info("Creating SQLAlchemy engine...")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=True  # Enable SQL query logging
    )
    logger.info("SQLAlchemy engine created successfully")
except Exception as e:
    logger.error(f"Failed to create SQLAlchemy engine: {str(e)}", exc_info=True)
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("Session factory created")

# Create base class for models
Base = declarative_base()
logger.info("Base class for models created")

async def test_db_connection():
    """Test database connection with timeout."""
    try:
        # Create a new session
        db = SessionLocal()
        try:
            # Set a timeout for the query
            db.execute(text("SET statement_timeout = '5s'"))
            # Simple query to test connection
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error creating database session: {str(e)}")
        return False

def get_db():
    """Get database session with logging."""
    logger.info("Getting database session...")
    db = SessionLocal()
    try:
        logger.info("Database session created successfully")
        yield db
    except Exception as e:
        logger.error(f"Error in database session: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Closing database session...")
        db.close()
        logger.info("Database session closed") 