from sqlalchemy.orm import Session
from .models import Checklist, Chore

def seed_database(db: Session):
    # Create checklists
    checklists_data = [
        {
            "name": "opening",
            "description": "Opening Checklist",
            "chores": [
                "Turn on all lights and music system",
                "Check and record fridge temperatures",
                "Fill ice bucket",
                "Clean and organize bar area",
                "Stock glasses and supplies",
                "Check beer lines and CO2 levels",
                "Prepare garnishes",
                "Count float and prepare till"
            ]
        },
        {
            "name": "closing",
            "description": "Closing Checklist",
            "chores": [
                "Clean all surfaces and equipment",
                "Empty and clean ice bins",
                "Restock bar for next shift",
                "Clean and organize glassware",
                "Empty trash bins",
                "Count and record till",
                "Turn off all equipment",
                "Set alarm and lock up"
            ]
        },
        {
            "name": "kitchen-opening",
            "description": "Kitchen Opening Checklist",
            "chores": [
                "Turn on all kitchen equipment",
                "Check and record freezer temperatures",
                "Prep mise en place",
                "Check stock levels",
                "Clean and sanitize work surfaces",
                "Prepare daily specials"
            ]
        },
        {
            "name": "kitchen-closing",
            "description": "Kitchen Closing Checklist",
            "chores": [
                "Clean and sanitize all surfaces",
                "Store and label leftover ingredients",
                "Clean and maintain equipment",
                "Empty and clean bins",
                "Sweep and mop floors",
                "Turn off all equipment"
            ]
        },
        {
            "name": "weekly",
            "description": "Weekly Cleaning",
            "chores": [
                "Deep clean beer lines",
                "Clean and organize storage areas",
                "Deep clean kitchen equipment",
                "Check and maintain safety equipment",
                "Clean windows and mirrors",
                "Deep clean bathrooms",
                "Update inventory records",
                "Check and maintain pest control"
            ]
        }
    ]

    # Add checklists and chores to database
    for checklist_data in checklists_data:
        checklist = Checklist(
            name=checklist_data["name"],
            description=checklist_data["description"]
        )
        db.add(checklist)
        db.flush()  # Get the checklist ID

        # Add chores for this checklist
        for order, description in enumerate(checklist_data["chores"], 1):
            chore = Chore(
                checklist_id=checklist.id,
                description=description,
                order=order
            )
            db.add(chore)

    db.commit()
    print("Database seeded successfully!") 