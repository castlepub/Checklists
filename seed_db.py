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
        kitchen_opening_checklist = Checklist(name="Kitchen Opening Checklist")
        kitchen_closing_checklist = Checklist(name="Kitchen Closing Checklist")
        weekly_cleaning_checklist = Checklist(name="Weekly Cleaning Checklist")
        
        db.add(opening_checklist)
        db.add(closing_checklist)
        db.add(kitchen_opening_checklist)
        db.add(kitchen_closing_checklist)
        db.add(weekly_cleaning_checklist)
        db.commit()
        
        # Opening checklist chores
        opening_chores = [
            ("Till", [
                "Count till to 250",
                "Count silver tin to 250"
            ]),
            ("Downstairs", [
                "Turn on Gas",
                "Fill a fresh ice bag",
                "Check bathrooms (soap, toilet paper)",
                "Empty run off bucket from kegroom"
            ]),
            ("Beergarden", [
                "Open all Marquee",
                "Ashtray on every table",
                "Wipe Tables clean",
                "Empty Glass Bins from behind bar into cage"
            ]),
            ("Bar", [
                "Sign into till (Admin user, code 4215)",
                "Fill ice bucket",
                "Set up long drinks station",
                "Turn on and set up dishwasher",
                "Turn on coffee machine",
                "Turn on pizza oven asap and extractor fan (n.1) - clean oven first",
                "Defrost and display muffins"
            ]),
            ("Floor", [
                "Open all doors",
                "Put A boards and ashtray outside",
                "Check and sweep floor",
                "Make sure there is two menus on every table",
                "Open Windows",
                "Put out reservations"
            ]),
            ("Prep for busy shifts / during shift", [
                "Bring up spare stock e.g. tonic, bestsellers",
                "Restock snacks, Pringles, Nuts",
                "Make Mexikaner if needed",
                "Check kegs in kegroom",
                "Put deliveries away",
                "Restock food",
                "Clean shelves, fridges glasswasher area",
                "Cut fruit and store",
                "Sweep Outside front, and garden"
            ])
        ]
        
        # Closing checklist chores
        closing_chores = [
            ("Beer Garden", [
                "Collect, empty all ashtrays in beer garden",
                "Close umbrellas, marquee",
                "Close doors at the front of the bar, windows and doors at the back at 10pm because of noise",
                "Empty beer garden bins",
                "Turn off lights and block off the back door at 10pm"
            ]),
            ("Stock up", [
                "Take pfand downstairs, sort into correct crates - The crates must be the same the bottles came in",
                "Fill ice bag ½ full and lie flat in freezer, so ice doesn't stick together",
                "Stock up all fridges, including wine, tonic, mixers and fridge drawers - 12 of each tonic flavour"
            ]),
            ("Floor", [
                "Check toilets are empty and restock toilet paper, empty bins, soap",
                "Correct all furniture that has been moved throughout shift",
                "Clean all tables (reset menus x2) and clean bar tops",
                "Sweep floors, mop spillages"
            ]),
            ("Street", [
                "Bring in A boards and big ashtray",
                "Close doors and lock",
                "Sweep street in front of doors"
            ]),
            ("Bar", [
                "Clean Coffee Machine (use cleaning tab on Sunday Night)",
                "Empty drip trays and clean. Put them back once dry. Clean surfaces underneath.",
                "Pour hot water down drain under taps",
                "Write down wastage on the google sheet",
                "Douche taps, wipe nozzles clean and clean tap handles using disinfectant spray.",
                "Turn off",
                "Clean all chopping boards, measures and ice bucket / scoop",
                "Drain dishwasher and clean filter, blades, insides including plug. Leave propped open so it airs out",
                "Sweep behind bar",
                "Take out all trash bags, cardboard",
                "Clean Sinks, including hand wash sink"
            ]),
            ("Cash", [
                "Count silver tin to 250 and sign sheet inside",
                "Print Shift Report",
                "All Staff Clock out of lightspeed",
                "Using Blue Ipad Open End of Day Link and input details after counting Cash downstairs",
                "Lock all cash including, silver tin, black ipad tin, downstairs in keg room - including the keys with fob"
            ]),
            ("Security", [
                "Turn off all lamps, remote lights, fans and main light switches near the beer taps.",
                "Check all doors and windows are closed and locked",
                "Double lock doors downstairs",
                "Security walk round, checking toilets and all windows/doors",
                "Check jobs not done on list haven't been signed and notifying the person opening"
            ])
        ]
        
        # Add opening chores
        for section, tasks in opening_chores:
            for i, task in enumerate(tasks):
                chore = Chore(
                    description=task,
                    section=section,
                    order=i,
                    checklist_id=opening_checklist.id
                )
                db.add(chore)
        
        # Add closing chores
        for section, tasks in closing_chores:
            for i, task in enumerate(tasks):
                chore = Chore(
                    description=task,
                    section=section,
                    order=i,
                    checklist_id=closing_checklist.id
                )
                db.add(chore)
        
        # Kitchen opening checklist chores
        kitchen_opening_chores = [
            ("Oven", [
                "Using wet cloth wipe doors and edges, removing any soot and grease",
                "Make sure oven is set to correct temperature",
                "Turn on extractor fan"
            ]),
            ("Fridges", [
                "Check dough and bring up more if its a busy day",
                "Look at stock of cheese and toppings and make note of any missing.",
                "Fill metal containers for the day",
                "Clean fridges, including the seal around door"
            ]),
            ("Prep area", [
                "Turn on lights above counter tops",
                "Place pizza cutters on plate",
                "Set up scoops and spoons above food area"
            ]),
            ("Prep for busy shifts / during shift", [
                "Bring up extra stock, ie Pizza Sauce, Cheese etc",
                "Put extra stock into plasic containers. *Write the expiry date on the lid*",
                "Organize fridges, ie bring food that is expiring first to the top.",
                "Fill flour and oil containers"
            ]),
            ("Temperature Checks", [
                "Temperature of Cheese Fridge in Stock room @15:00"
            ])
        ]

        # Add kitchen opening chores
        for section, tasks in kitchen_opening_chores:
            for i, task in enumerate(tasks):
                chore = Chore(
                    description=task,
                    section=section,
                    order=i,
                    checklist_id=kitchen_opening_checklist.id
                )
                db.add(chore)
        
        # Kitchen closing checklist chores
        kitchen_closing_chores = [
            ("Oven", [
                "Clean oven using the brush",
                "Turn off oven",
                "Turn off extractor fan"
            ]),
            ("Prep Area", [
                "Remove all pizza cutters, spoons etc and place in dishwasher",
                "Remove lids from metal containers and place in dishwasher",
                "Remove containers from fridge and wash any empty or dirty ones in dishwasher",
                "Clean inside the fridge area with tissue, removing any food bits and excess water",
                "Using a damp cloth clean the rims and outside of containers",
                "Cover containers with clingfilm",
                "Place containers back in fridge and cover with lids",
                "Clean inside the microwave with sanitizer",
                "Spray down prep area with sanitizer and wipe using cloth",
                "Place pizza cutters and utentils back"
            ]),
            ("Fridge", [
                "Bring up and bag dough (at least 50)",
                "Wipe down inside of fridges of crumbs, and disinfect handles",
                "Clean Pizza Shovel"
            ]),
            ("Floor/miscellaneous", [
                "Sweep floor of any flour and food. (under fridges too)",
                "Check all areas have been cleaned of all food and flour",
                "Turn off Lights over prep area"
            ])
        ]

        # Add kitchen closing chores
        for section, tasks in kitchen_closing_chores:
            for i, task in enumerate(tasks):
                chore = Chore(
                    description=task,
                    section=section,
                    order=i,
                    checklist_id=kitchen_closing_checklist.id
                )
                db.add(chore)
        
        # Weekly cleaning checklist chores
        weekly_cleaning_chores = [
            ("Food", [
                "Clean all inside and outside fridges, handles, and seals",
                "- Cheese Fridge - Sauce Fridge",
                "- Fruit fridge - Dough fridge - Ice freezer.",
                "Deep clean salad bar, remove all water collected inside",
                "Clean inside, underneath microwave",
                "Oven, underneath, top, buttons, glass doors",
                "Clean the oven ventilation hood",
                "Deep clean the Air fryers",
                "Replace pizza mop head with new one",
                "Wash dirty cloths and aprons"
            ]),
            ("Cellar", [
                "Collect all trash from keg room and office desk",
                "Clean ice machine, scoop, area in general and chest freezer",
                "Tidy Pfand/stock room",
                "Organise keg room downstairs, clean floor, pipes",
                "Clean ALL couplers"
            ]),
            ("Floor", [
                "Clean green tiles at the bar and side bar",
                "Clean glass of fridges, and handles using Glass Cleaner!!",
                "Dust all light bulbs and lamps",
                "Water houseplants, check with finger if soil is dry first at least 1inch deep",
                "Cobwebs from corners",
                "Replace Menus with new clean ones"
            ]),
            ("Street / Outside", [
                "Deep sweep garden, wipe bins clean, remove trash from flower beds",
                "Sweep around the building, front and side",
                "Re-design A boards (Once per week)"
            ]),
            ("Bar", [
                "Deep clean sink area",
                "Take apart all parts of glass washer, scrub the inside and outside",
                "Clean all glass shelves, wash mats - Wine Glass Shelf",
                "- Gin Glass, Shot Glass shelf",
                "- Pint Glass shelf, including shelves underneath",
                "Dust all gin bottles and bottle shelves",
                "Clean all fridge shelves and doors, handles, fridge seals",
                "- Spirit Drawer - Mixer Drawer",
                "- Prosecco Fridge - Tonic Fridge",
                "- Wine Fridge - Black Drawers - Milk Drawer",
                "Polish taps",
                "Coffee Machine Area - Dust shelves, syrup bottles etc",
                "Deep Clean Coffee Machine",
                "Vacuum and Clean all fridge filters - especially food fridge"
            ])
        ]

        # Add weekly cleaning chores
        for section, tasks in weekly_cleaning_chores:
            for i, task in enumerate(tasks):
                chore = Chore(
                    description=task,
                    section=section,
                    order=i,
                    checklist_id=weekly_cleaning_checklist.id
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