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
    
    try:
        # Create checklists
        opening = Checklist(name="opening", description="Opening Checklist")
        closing = Checklist(name="closing", description="Closing Checklist")
        weekly = Checklist(name="weekly", description="Weekly Checklist")
        kitchen_opening = Checklist(name="kitchen_opening", description="Kitchen Opening Checklist")
        kitchen_closing = Checklist(name="kitchen_closing", description="Kitchen Closing Checklist")
        
        db.add_all([opening, closing, weekly, kitchen_opening, kitchen_closing])
        db.commit()

        # Create sections for opening checklist
        opening_sections = [
            Section(checklist_id=opening.id, name="Till", order=1),
            Section(checklist_id=opening.id, name="Floor", order=2),
            Section(checklist_id=opening.id, name="Prep", order=3),
            Section(checklist_id=opening.id, name="Bar", order=4),
            Section(checklist_id=opening.id, name="Kitchen", order=5)
        ]
        db.add_all(opening_sections)
        db.commit()

        # Create sections for closing checklist
        closing_sections = [
            Section(checklist_id=closing.id, name="Till", order=1),
            Section(checklist_id=closing.id, name="Floor", order=2),
            Section(checklist_id=closing.id, name="Bar", order=3),
            Section(checklist_id=closing.id, name="Kitchen", order=4)
        ]
        db.add_all(closing_sections)
        db.commit()

        # Create sections for weekly checklist
        weekly_sections = [
            Section(checklist_id=weekly.id, name="Bar Deep Clean", order=1),
            Section(checklist_id=weekly.id, name="Kitchen Deep Clean", order=2),
            Section(checklist_id=weekly.id, name="Floor Deep Clean", order=3),
            Section(checklist_id=weekly.id, name="Storage Areas", order=4)
        ]
        db.add_all(weekly_sections)
        db.commit()

        # Create sections for kitchen opening checklist
        kitchen_opening_sections = [
            Section(checklist_id=kitchen_opening.id, name="Equipment Check", order=1),
            Section(checklist_id=kitchen_opening.id, name="Food Prep", order=2),
            Section(checklist_id=kitchen_opening.id, name="Safety Check", order=3)
        ]
        db.add_all(kitchen_opening_sections)
        db.commit()

        # Create sections for kitchen closing checklist
        kitchen_closing_sections = [
            Section(checklist_id=kitchen_closing.id, name="Equipment Cleaning", order=1),
            Section(checklist_id=kitchen_closing.id, name="Storage", order=2),
            Section(checklist_id=kitchen_closing.id, name="Final Checks", order=3)
        ]
        db.add_all(kitchen_closing_sections)
        db.commit()

        # Create chores for opening checklist
        opening_chores = [
            # Till section
            Chore(checklist_id=opening.id, section_id=opening_sections[0].id, description="Count float", order=1),
            Chore(checklist_id=opening.id, section_id=opening_sections[0].id, description="Check card machine", order=2),
            Chore(checklist_id=opening.id, section_id=opening_sections[0].id, description="Check till roll", order=3),

            # Floor section
            Chore(checklist_id=opening.id, section_id=opening_sections[1].id, description="Check tables are clean", order=1),
            Chore(checklist_id=opening.id, section_id=opening_sections[1].id, description="Check chairs are clean", order=2),
            Chore(checklist_id=opening.id, section_id=opening_sections[1].id, description="Check floor is clean", order=3),
            Chore(checklist_id=opening.id, section_id=opening_sections[1].id, description="Check toilets are clean", order=4),

            # Prep section
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Cut lemons", order=1),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Cut limes", order=2),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Cut oranges", order=3),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check garnish tray", order=4),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check straws", order=5),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check napkins", order=6),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check coasters", order=7),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check ice", order=8),
            Chore(checklist_id=opening.id, section_id=opening_sections[2].id, description="Check menus", order=9),

            # Bar section
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check beer lines", order=1),
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check spirit bottles", order=2),
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check wine bottles", order=3),
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check fridges", order=4),
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check glass washer", order=5),
            Chore(checklist_id=opening.id, section_id=opening_sections[3].id, description="Check glasses are clean", order=6),

            # Kitchen section
            Chore(checklist_id=opening.id, section_id=opening_sections[4].id, description="Check fridge temperatures", order=1),
            Chore(checklist_id=opening.id, section_id=opening_sections[4].id, description="Check freezer temperatures", order=2),
            Chore(checklist_id=opening.id, section_id=opening_sections[4].id, description="Check food prep area", order=3),
            Chore(checklist_id=opening.id, section_id=opening_sections[4].id, description="Check cleaning supplies", order=4)
        ]
        db.add_all(opening_chores)
        db.commit()

        # Create chores for closing checklist
        closing_chores = [
            # Till section
            Chore(checklist_id=closing.id, section_id=closing_sections[0].id, description="Count till", order=1),
            Chore(checklist_id=closing.id, section_id=closing_sections[0].id, description="Print Z report", order=2),
            Chore(checklist_id=closing.id, section_id=closing_sections[0].id, description="Lock till", order=3),

            # Floor section
            Chore(checklist_id=closing.id, section_id=closing_sections[1].id, description="Clean tables", order=1),
            Chore(checklist_id=closing.id, section_id=closing_sections[1].id, description="Clean chairs", order=2),
            Chore(checklist_id=closing.id, section_id=closing_sections[1].id, description="Sweep floor", order=3),
            Chore(checklist_id=closing.id, section_id=closing_sections[1].id, description="Mop floor", order=4),
            Chore(checklist_id=closing.id, section_id=closing_sections[1].id, description="Clean toilets", order=5),

            # Bar section
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean beer lines", order=1),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean spirit bottles", order=2),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean wine bottles", order=3),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean fridges", order=4),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean glass washer", order=5),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Clean glasses", order=6),
            Chore(checklist_id=closing.id, section_id=closing_sections[2].id, description="Empty ice well", order=7),

            # Kitchen section
            Chore(checklist_id=closing.id, section_id=closing_sections[3].id, description="Clean food prep area", order=1),
            Chore(checklist_id=closing.id, section_id=closing_sections[3].id, description="Clean surfaces", order=2),
            Chore(checklist_id=closing.id, section_id=closing_sections[3].id, description="Empty bins", order=3),
            Chore(checklist_id=closing.id, section_id=closing_sections[3].id, description="Check fridge temperatures", order=4)
        ]
        db.add_all(closing_chores)
        db.commit()

        # Create chores for weekly checklist
        weekly_chores = [
            # Bar Deep Clean section
            Chore(checklist_id=weekly.id, section_id=weekly_sections[0].id, description="Clean beer lines thoroughly", order=1),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[0].id, description="Deep clean all bar equipment", order=2),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[0].id, description="Clean and organize liquor storage", order=3),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[0].id, description="Deep clean ice machines", order=4),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[0].id, description="Clean and maintain beer taps", order=5),

            # Kitchen Deep Clean section
            Chore(checklist_id=weekly.id, section_id=weekly_sections[1].id, description="Deep clean ovens", order=1),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[1].id, description="Clean hood vents", order=2),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[1].id, description="Deep clean fridges", order=3),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[1].id, description="Clean and sanitize prep areas", order=4),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[1].id, description="Deep clean dishwasher", order=5),

            # Floor Deep Clean section
            Chore(checklist_id=weekly.id, section_id=weekly_sections[2].id, description="Deep clean all floor areas", order=1),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[2].id, description="Clean baseboards", order=2),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[2].id, description="Clean walls", order=3),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[2].id, description="Clean ceiling vents", order=4),

            # Storage Areas section
            Chore(checklist_id=weekly.id, section_id=weekly_sections[3].id, description="Organize storage rooms", order=1),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[3].id, description="Check inventory", order=2),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[3].id, description="Clean and organize cellar", order=3),
            Chore(checklist_id=weekly.id, section_id=weekly_sections[3].id, description="Check for any maintenance needs", order=4)
        ]
        db.add_all(weekly_chores)
        db.commit()

        # Create chores for kitchen opening checklist
        kitchen_opening_chores = [
            # Equipment Check section
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[0].id, description="Turn on all equipment", order=1),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[0].id, description="Check fridge temperatures", order=2),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[0].id, description="Check freezer temperatures", order=3),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[0].id, description="Check equipment functionality", order=4),

            # Food Prep section
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[1].id, description="Check food inventory", order=1),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[1].id, description="Prepare mise en place", order=2),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[1].id, description="Check prep list", order=3),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[1].id, description="Prepare sauces", order=4),

            # Safety Check section
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[2].id, description="Check fire safety equipment", order=1),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[2].id, description="Check first aid kit", order=2),
            Chore(checklist_id=kitchen_opening.id, section_id=kitchen_opening_sections[2].id, description="Check cleaning supplies", order=3)
        ]
        db.add_all(kitchen_opening_chores)
        db.commit()

        # Create chores for kitchen closing checklist
        kitchen_closing_chores = [
            # Equipment Cleaning section
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[0].id, description="Clean and sanitize all surfaces", order=1),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[0].id, description="Clean cooking equipment", order=2),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[0].id, description="Clean and empty fryers", order=3),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[0].id, description="Clean hood filters", order=4),

            # Storage section
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[1].id, description="Store prepped items properly", order=1),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[1].id, description="Label and date all items", order=2),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[1].id, description="Rotate stock", order=3),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[1].id, description="Check storage temperatures", order=4),

            # Final Checks section
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[2].id, description="Turn off all equipment", order=1),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[2].id, description="Empty all bins", order=2),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[2].id, description="Lock all storage areas", order=3),
            Chore(checklist_id=kitchen_closing.id, section_id=kitchen_closing_sections[2].id, description="Final kitchen inspection", order=4)
        ]
        db.add_all(kitchen_closing_chores)
        db.commit()

        # Create staff members
        staff_members = [
            Staff(name="Nora"),
            Staff(name="Josh"),
            Staff(name="Vaile"),
            Staff(name="Melissa"),
            Staff(name="Paddy"),
            Staff(name="Pero"),
            Staff(name="Guy"),
            Staff(name="Dean"),
            Staff(name="Bethany"),
            Staff(name="Henry")
        ]
        db.add_all(staff_members)
        db.commit()

        logger.info("Database seeded successfully!")
    except Exception as e:
        logger.error(f"Error committing database changes: {str(e)}", exc_info=True)
        db.rollback()
        raise 