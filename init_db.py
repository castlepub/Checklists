from app.models import Base
from app.database import engine, SessionLocal
from app.seed_data import seed_database
from dotenv import load_dotenv
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    load_dotenv()
    
    # Add retry logic for database initialization
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database initialization (attempt {attempt + 1}/{max_retries})")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully!")
            
            # Seed the database with initial data
            db = SessionLocal()
            try:
                seed_database(db)
                logger.info("Database seeded successfully!")
                break
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if attempt < max_retries - 1:
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("All database initialization attempts failed")
                raise

if __name__ == "__main__":
    init_database() 