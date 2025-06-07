from app.models import Base
from app.database import engine, SessionLocal
from app.seed_data import seed_database
from dotenv import load_dotenv

def init_database():
    load_dotenv()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    # Seed the database with initial data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 