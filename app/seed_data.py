from sqlalchemy.orm import Session
from .models import Checklist, Chore

def seed_database(db: Session):
    # Create staff members
    staff_names = [
        "Nora", "Josh", "Vaile", "Melissa", "Paddy",
        "Pero", "Guy", "Dean", "Bethany", "Henry"
    ]

    # Create checklists
    checklists_data = [
        {
            "name": "opening",
            "description": "Opening Checklist",
            "chores": [
                # Till
                "Count till to 250",
                "Count silver tin to 250",
                
                # Downstairs
                "Turn on Gas",
                "Fill a fresh ice bag",
                "Check bathrooms (soap, toilet paper)",
                "Empty run off bucket from kegroom",
                
                # Beergarden
                "Open all Marquee",
                "Ashtray on every table",
                "Wipe Tables clean",
                "Empty Glass Bins from behind bar into cage",
                
                # Bar
                "Sign into till (Admin user, code 4215)",
                "Fill ice bucket",
                "Set up long drinks station",
                "Turn on and set up dishwasher",
                "Turn on coffee machine",
                "Turn on pizza oven asap and extractor fan (n.1) - clean oven first",
                "Defrost and display muffins",
                
                # Floor
                "Open all doors",
                "Put A boards and ashtray outside",
                "Check and sweep floor",
                "Make sure there is two menus on every table",
                "Open Windows",
                "Put out reservations",
                
                # Prep for busy shifts / during shift
                "Bring up spare stock e.g. tonic, bestsellers",
                "Restock snacks, Pringles, Nuts",
                "Make Mexikaner if needed",
                "Check kegs in kegroom",
                "Put deliveries away",
                "Restock food",
                "Clean shelves, fridges glasswasher area",
                "Cut fruit and store",
                "Sweep Outside front, and garden"
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