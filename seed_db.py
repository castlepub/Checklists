from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Checklist, Chore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database engine
engine = create_engine(os.getenv('DATABASE_URL'))
SessionLocal = sessionmaker(bind=engine)

def seed_database():
    print("Starting database seeding...")
    
    # Create tables
    print("Creating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create checklists
        opening_checklist = Checklist(name="Opening Checklist")
        closing_checklist = Checklist(name="Closing Checklist")
        
        db.add(opening_checklist)
        db.add(closing_checklist)
        db.commit()
        
        # Opening checklist chores
        opening_chores = [
            ("Bar Setup", [
                "Turn on all tills",
                "Check float is correct",
                "Turn on all beer taps",
                "Check gas is on",
                "Check ice wells are full",
                "Check fridges are stocked",
                "Prepare garnishes",
                "Check bar is clean and organized"
            ]),
            ("Kitchen Setup", [
                "Turn on all equipment",
                "Check temperatures are correct",
                "Prepare mise en place",
                "Check stock levels",
                "Clean and sanitize work surfaces"
            ]),
            ("Front of House", [
                "Turn on music system",
                "Check all tables are clean",
                "Put out clean ashtrays",
                "Check bathrooms are clean",
                "Put out table numbers",
                "Check menus are clean"
            ]),
            ("Safety Checks", [
                "Check emergency exits are clear",
                "Check first aid kit is complete",
                "Test emergency lighting",
                "Check fire extinguishers",
                "Ensure all safety signs are visible"
            ])
        ]
        
        # Closing checklist chores
        closing_chores = [
            ("Bar Closing", [
                "Clean all beer lines",
                "Turn off beer taps",
                "Clean bar surface",
                "Empty ice wells",
                "Restock fridges",
                "Count and secure float",
                "Turn off tills"
            ]),
            ("Kitchen Closing", [
                "Clean all equipment",
                "Store all food properly",
                "Clean and sanitize surfaces",
                "Empty bins",
                "Check temperatures",
                "Turn off equipment"
            ]),
            ("Front of House", [
                "Clean and reset tables",
                "Vacuum/sweep floors",
                "Clean bathrooms",
                "Empty all bins",
                "Turn off music system",
                "Collect and clean ashtrays"
            ]),
            ("Security", [
                "Check all windows are locked",
                "Check all doors are locked",
                "Set alarm",
                "Turn off non-essential power",
                "Secure all valuables"
            ])
        ]
        
        # Add opening chores
        for section, tasks in opening_chores:
            for task in tasks:
                chore = Chore(
                    description=task,
                    section=section,
                    checklist_id=opening_checklist.id
                )
                db.add(chore)
        
        # Add closing chores
        for section, tasks in closing_chores:
            for task in tasks:
                chore = Chore(
                    description=task,
                    section=section,
                    checklist_id=closing_checklist.id
                )
                db.add(chore)
        
        # Commit all changes
        db.commit()
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 