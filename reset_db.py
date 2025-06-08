from app.models import Base
from app.database import engine, SessionLocal
from app.seed_data import seed_database
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    load_dotenv()
    
    try:
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully!")
        
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
        
        # Seed the database with initial data
        db = SessionLocal()
        try:
            seed_database(db)
            logger.info("Database seeded successfully!")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

if __name__ == "__main__":
    reset_database() 