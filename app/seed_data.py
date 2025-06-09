from sqlalchemy.orm import Session
from .models import Checklist, Section, Chore, ChoreCompletion, Staff
import logging

# Configure logging
logger = logging.getLogger(__name__)

def seed_database(db: Session):
    """Seed the database with initial data."""
    logger.info("Starting database seeding...")
    
    # Delete all existing data
    db.query(ChoreCompletion).delete()
    db.query(Chore).delete()
    db.query(Section).delete()
    db.query(Checklist).delete()
    db.query(Staff).delete()
    db.commit()
    
    # Create staff members
    staff_names = [
        "Nora", "Josh", "Vaile", "Melissa", "Paddy",
        "Pero", "Guy", "Dean", "Bethany", "Henry"
    ]
    logger.info(f"Adding {len(staff_names)} staff members...")
    
    for name in staff_names:
        staff = Staff(name=name, is_active=True)
        db.add(staff)
    db.commit()
    logger.info("Staff members added successfully")

    # Create checklists with sections and chores
    checklists_data = [
        {
            "name": "opening",
            "description": "Opening Checklist - Sign your initials when task is completed.",
            "sections": [
                {
                    "name": "Till",
                    "chores": [
                        "Count till to 250",
                        "Count silver tin to 250"
                    ]
                },
                {
                    "name": "Downstairs",
                    "chores": [
                        "Turn on Gas",
                        "Fill a fresh ice bag",
                        "Check bathrooms (soap, toilet paper)",
                        "Empty run off bucket from kegroom"
                    ]
                },
                {
                    "name": "Beergarden",
                    "chores": [
                        "Open all Marquee",
                        "Ashtray on every table",
                        "Wipe Tables clean",
                        "Empty Glass Bins from behind bar into cage"
                    ]
                },
                {
                    "name": "Bar",
                    "chores": [
                        "Sign into till (Admin user, code 4215)",
                        "Fill ice bucket",
                        "Set up long drinks station",
                        "Turn on and set up dishwasher",
                        "Turn on coffee machine",
                        "Turn on pizza oven asap and extractor fan (n.1) - clean oven first",
                        "Defrost and display muffins"
                    ]
                },
                {
                    "name": "Floor",
                    "chores": [
                        "Open all doors",
                        "Put A boards and ashtray outside",
                        "Check and sweep floor",
                        "Make sure there is two menus on every table",
                        "Open Windows",
                        "Put out reservations"
                    ]
                },
                {
                    "name": "Prep",
                    "chores": [
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
                }
            ]
        },
        {
            "name": "closing",
            "description": "Closing Checklist",
            "sections": [
                {
                    "name": "Beer Garden",
                    "chores": [
                        "Collect, empty all ashtrays in beer garden",
                        "Close umbrellas, marquee",
                        "Close doors at the front of the bar, windows and doors at the back at 10pm because of noise",
                        "Empty beer garden bins",
                        "Turn off lights and block off the back door at 10pm"
                    ]
                },
                {
                    "name": "Stock",
                    "chores": [
                        "Take pfand downstairs, sort into correct crates - The crates must be the same the bottles came in",
                        "Fill ice bag ⅓ full and lie flat in freezer, so ice doesn't stick together",
                        "Stock up all fridges, including wine, tonic, mixers and fridge drawers - 12 of each tonic flavour"
                    ]
                },
                {
                    "name": "Floor",
                    "chores": [
                        "Check toilets are empty and restock toilet paper, empty bins, soap",
                        "Correct all furniture that has been moved throughout shift",
                        "Clean all tables (reset menus x2) and clean bar tops",
                        "Sweep floors, mop spillages"
                    ]
                },
                {
                    "name": "Street",
                    "chores": [
                        "Bring in A boards and big ashtray",
                        "Close doors and lock",
                        "Sweep street in front of doors"
                    ]
                },
                {
                    "name": "Bar",
                    "chores": [
                        "Clean Coffee Machine (use cleaning tab on Sunday Night)",
                        "Empty drip trays and clean. Put them back once dry. Clean surfaces underneath. Pour hot water down drain under taps",
                        "Write down wastage on the google sheet",
                        "Douche taps, wipe nozzles clean and clean tap handles using disinfectant spray. Turn off",
                        "Clean all chopping boards, measures and ice bucket / scoop",
                        "Drain dishwasher and clean filter, blades, insides including plug. Leave propped open so it airs out",
                        "Sweep behind bar",
                        "Take out all trash bags, cardboard",
                        "Clean Sinks, including hand wash sink"
                    ]
                },
                {
                    "name": "Cash",
                    "chores": [
                        "Count silver tin to 250 and sign sheet inside",
                        "Print Shift Report",
                        "All Staff Clock out of lightspeed",
                        "Using Blue Ipad Open End of Day Link and input details after counting Cash downstairs",
                        "Lock all cash including, silver tin, black ipad tin, downstairs in keg room - including the keys with fob"
                    ]
                },
                {
                    "name": "Final",
                    "chores": [
                        "Turn off all lamps, remote lights, fans and main light switches near the beer taps.",
                        "Check all doors and windows are closed and locked",
                        "Double lock doors downstairs",
                        "Security walk round, checking toilets and all windows/doors",
                        "Check jobs not done on list haven't been signed and notifying the person opening"
                    ]
                }
            ]
        },
        {
            "name": "kitchen-opening",
            "description": "Kitchen Opening Checklist - Sign your initials when task is completed.",
            "sections": [
                {
                    "name": "Oven",
                    "chores": [
                        "Using wet cloth wipe doors and edges, removing any soot and grease",
                        "Make sure oven is set to correct temperature",
                        "Turn on extractor fan"
                    ]
                },
                {
                    "name": "Fridges",
                    "chores": [
                        "Check dough and bring up more if its a busy day",
                        "Look at stock of cheese and toppings and make note of any missing.",
                        "Fill metal containers for the day",
                        "Clean fridges, including the seal around door"
                    ]
                },
                {
                    "name": "Prep",
                    "chores": [
                        "Turn on lights above counter tops",
                        "Place pizza cutters on plate",
                        "Set up scoops and spoons above food area"
                    ]
                },
                {
                    "name": "Stock",
                    "chores": [
                        "Bring up extra stock, ie Pizza Sauce, Cheese etc",
                        "Put extra stock into plasic containers. *Write the expiry date on the lid*",
                        "Organize fridges, ie bring food that is expiring first to the top.",
                        "Fill flour and oil containers"
                    ]
                },
                {
                    "name": "Temp",
                    "chores": [
                        "Temperature of Cheese Fridge in Stock room @15:00"
                    ]
                }
            ]
        },
        {
            "name": "kitchen-closing",
            "description": "Kitchen Closing Checklist",
            "sections": [
                {
                    "name": "Oven",
                    "chores": [
                        "Clean oven using the brush",
                        "Turn off oven",
                        "Turn off extractor fan"
                    ]
                },
                {
                    "name": "Prep",
                    "chores": [
                        "Remove all pizza cutters, spoons etc and place in dishwasher",
                        "Remove lids from metal containers and place in dishwasher",
                        "Remove containers from fridge and wash any empty or dirty ones in dishwasher",
                        "Clean inside the fridge area with tissue, removing any food bits and excess water",
                        "Using a damp cloth clean the rims and outside of containers",
                        "Cover containers with clingfilm",
                        "Place containers back in fridge and cover with lids",
                        "Clean inside the microwave with sanitzer",
                        "Spray down prep area with sanitizer and wipe using cloth",
                        "Place pizza cutters and utenils back"
                    ]
                },
                {
                    "name": "Fridge",
                    "chores": [
                        "Bring up and bag dough (at least 50)",
                        "Wipe down inside of fridges of crumbs, and disinfect handles",
                        "Clean Pizza Shovel"
                    ]
                },
                {
                    "name": "Floor",
                    "chores": [
                        "Sweep floor of any flour and food. (under fridges too)",
                        "Check all areas have been cleaned of all food and flour",
                        "Turn off Lights over prep area"
                    ]
                }
            ]
        },
        {
            "name": "weekly",
            "description": "Weekly Cleaning - ONE JOB EACH PER SHIFT MINIMUM",
            "sections": [
                {
                    "name": "Food",
                    "chores": [
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
                    ]
                },
                {
                    "name": "Cellar",
                    "chores": [
                        "Collect all trash from keg room and office desk",
                        "Clean ice machine, scoop, area in general and chest freezer",
                        "Tidy Pfand/stock room",
                        "Organise keg room downstairs, clean floor, pipes",
                        "Clean ALL couplers"
                    ]
                },
                {
                    "name": "Floor",
                    "chores": [
                        "Clean green tiles at the bar and side bar",
                        "Clean glass of fridges, and handles using Glass Cleaner!!",
                        "Dust all light bulbs and lamps",
                        "Water houseplants, check with finger if soil is dry first at least 1inch deep",
                        "Cobwebs from corners",
                        "Replace Menus with new clean ones"
                    ]
                },
                {
                    "name": "Outside",
                    "chores": [
                        "Deep sweep garden, wipe bins clean, remove trash from flower beds",
                        "Sweep around the building, front and side",
                        "Re-design A boards (Once per week)"
                    ]
                },
                {
                    "name": "Bar",
                    "chores": [
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
                    ]
                }
            ]
        }
    ]

    # Add checklists, sections, and chores to database
    for checklist_data in checklists_data:
        logger.info(f"Creating checklist: {checklist_data['name']}")
        checklist = Checklist(
            name=checklist_data["name"],
            description=checklist_data["description"]
        )
        db.add(checklist)
        db.flush()  # Get the checklist ID
        logger.info(f"Created checklist with ID: {checklist.id}")

        # Add sections for this checklist
        for section_order, section_data in enumerate(checklist_data["sections"], 1):
            logger.info(f"Creating section: {section_data['name']} for checklist {checklist.name}")
            section = Section(
                checklist_id=checklist.id,
                name=section_data["name"],
                order=section_order
            )
            db.add(section)
            db.flush()  # Get the section ID
            logger.info(f"Created section with ID: {section.id}")

            # Add chores for this section
            for chore_order, description in enumerate(section_data["chores"], 1):
                logger.info(f"Creating chore: {description} for section {section.name}")
                chore = Chore(
                    checklist_id=checklist.id,
                    section_id=section.id,
                    description=description,
                    order=chore_order
                )
                db.add(chore)

    try:
        db.commit()
        logger.info("Database seeded successfully!")
    except Exception as e:
        logger.error(f"Error committing database changes: {str(e)}", exc_info=True)
        db.rollback()
        raise 