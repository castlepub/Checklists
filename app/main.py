from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, time, timedelta
import os
import asyncio
from contextlib import asynccontextmanager
import logging
import pytz
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import get_db, engine, Base, test_db_connection, SessionLocal
from .models import Checklist, Chore, ChoreCompletion, Signature, Section, Staff
from .telegram import telegram, cet_tz
from .seed_data import seed_database

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Constants for reset times
RESET_START_TIME = time(6, 0)  # 6:00 AM
RESET_END_TIME = time(8, 0)    # 8:00 AM

# Global variables to track application state
is_db_ready = False
db_init_error = None
startup_time = datetime.now()
STARTUP_GRACE_PERIOD = 60  # seconds

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def is_within_startup_grace_period() -> bool:
    """Check if we're still within the startup grace period"""
    return (datetime.now() - startup_time).total_seconds() < STARTUP_GRACE_PERIOD

def is_within_reset_window(current_time: time) -> bool:
    """Check if current time is within the reset window (6:00-8:00 AM)"""
    return RESET_START_TIME <= current_time <= RESET_END_TIME

def get_last_reset_time(now: datetime = None) -> datetime:
    """Get the timestamp of the last reset"""
    if now is None:
        now = datetime.now(pytz.UTC)
    
    # If we're in the reset window, use yesterday's reset time
    if is_within_reset_window(now.time()):
        now = now - timedelta(days=1)
    
    # Set to the last reset time (6:00 AM)
    last_reset = now.replace(hour=6, minute=0, second=0, microsecond=0)
    return last_reset

def get_last_weekly_reset_time(now: datetime = None) -> datetime:
    """Get the timestamp of the last weekly reset (Monday 6:00 AM)"""
    if now is None:
        now = datetime.now(pytz.UTC)
    
    # Calculate days since last Monday
    days_since_monday = now.weekday()
    
    # If it's Monday and we're in the reset window, use last week's reset time
    if days_since_monday == 0 and is_within_reset_window(now.time()):
        days_since_monday = 7
    
    # Get last Monday's reset time
    last_reset = now - timedelta(days=days_since_monday)
    last_reset = last_reset.replace(hour=6, minute=0, second=0, microsecond=0)
    return last_reset

async def init_db():
    global is_db_ready, db_init_error
    logger.info("Database initialization attempt started")
    max_attempts = 5
    attempt = 1
    while attempt <= max_attempts:
        try:
            logger.info(f"Database initialization attempt {attempt}/{max_attempts}")
            
            # First test the connection
            logger.info("Testing database connection...")
            await test_db_connection()
            logger.info("Database connection successful")
            
            # Create all tables
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            
            # Now check if we need to seed the database
            db = SessionLocal()
            try:
                # Check if tables exist by querying the checklists table
                try:
                    result = db.execute(text("SELECT COUNT(*) FROM checklists"))
                    count = result.scalar()
                    if count == 0:
                        logger.info("Database is empty, seeding initial data...")
                        seed_database(db)
                        db.commit()
                        logger.info("Database seeded successfully")
                    else:
                        logger.info(f"Database already contains {count} checklists, skipping seeding")
                except Exception as table_error:
                    if "relation" in str(table_error) and "does not exist" in str(table_error):
                        logger.info("Tables don't exist, creating and seeding database...")
                        Base.metadata.create_all(bind=engine)
                        seed_database(db)
                        db.commit()
                        logger.info("Database created and seeded successfully")
                    else:
                        raise
                
                is_db_ready = True
                db_init_error = None
                return  # Success - exit the function
            except Exception as e:
                logger.error(f"Error during database check/seeding: {str(e)}")
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database initialization attempt {attempt} failed: {str(e)}")
            if attempt < max_attempts:
                logger.info("Retrying database initialization in 5 seconds...")
                await asyncio.sleep(5)
                attempt += 1
            else:
                logger.error("All database initialization attempts failed")
                is_db_ready = False
                db_init_error = str(e)
                raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    logger.info("Application startup initiated")
    
    # Start database initialization in the background
    init_task = asyncio.create_task(init_db())
    
    yield
    
    # Application shutdown
    logger.info("Application shutdown initiated")
    engine.dispose()
    logger.info("Database connections disposed")

app = FastAPI(
    title="Castle Checklist App",
    lifespan=lifespan,
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Exception handler for 500 errors
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error, please try again later"}
    )

# Pydantic models
class ChoreBase(BaseModel):
    description: str
    order: int

class ChoreResponse(ChoreBase):
    id: int
    completed: bool = False
    comment: Optional[str] = None

class ChoreCompletionRequest(BaseModel):
    chore_id: int
    staff_name: str
    completed: bool

class ChoreCommentRequest(BaseModel):
    chore_id: int
    comment: str

class ChecklistSubmission(BaseModel):
    checklist_id: str
    staff_name: str
    signature_data: str

class TelegramUpdate(BaseModel):
    """Simplified Telegram Update model"""
    update_id: int
    message: Optional[dict] = None

# Health check endpoint for Railway
@app.get("/up")
async def health_check():
    """
    Main health check endpoint that Railway uses to determine if the service is healthy.
    Returns 200 OK during startup grace period or if database is ready and connected.
    """
    global is_db_ready, db_init_error
    
    # Log the health check request
    logger.info("Health check request received at /up")
    logger.info(f"Database ready: {is_db_ready}, Init error: {db_init_error}")
    
    # During startup grace period, always return OK
    if is_within_startup_grace_period():
        logger.info("Within startup grace period - returning OK")
        return {"status": "ok", "message": "Application starting"}
    
    # If database initialization failed, return error
    if db_init_error is not None:
        logger.error(f"Health check failed - DB init error: {db_init_error}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "detail": f"Database initialization failed: {db_init_error}"
            }
        )
    
    # If database is not ready yet, return service unavailable
    if not is_db_ready:
        logger.warning("Health check - DB not ready yet")
        return JSONResponse(
            status_code=503,
            content={
                "status": "initializing",
                "detail": "Database initialization in progress"
            }
        )
    
    # Test current database connection
    try:
        db = SessionLocal()
        try:
            # Simple query to test connection
            db.execute(text("SELECT 1"))
            logger.info("Health check passed - DB connection successful")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Health check DB query failed: {str(e)}")
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Health check failed - DB connection error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "detail": "Database connection test failed"
            }
        )

# Root endpoint
@app.get("/")
async def root(request: Request):
    # Return HTML response
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/checklists/{checklist_name}/chores")
async def get_checklist_chores(checklist_name: str, db: Session = Depends(get_db)):
    checklist = db.query(Checklist).filter(Checklist.name == checklist_name).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Get all chores for the checklist
    chores = db.query(Chore).filter(Chore.checklist_id == checklist.id).order_by(Chore.order).all()
    
    # Get the appropriate reset time based on checklist type
    now = datetime.now(pytz.UTC)
    if checklist_name == "weekly":
        reset_time = get_last_weekly_reset_time(now)
    else:
        reset_time = get_last_reset_time(now)
    
    # Get completions since last reset
    chore_states = []
    for chore in chores:
        # Get the latest completion for this chore since the last reset
        latest_completion = db.query(ChoreCompletion).filter(
            and_(
                ChoreCompletion.chore_id == chore.id,
                ChoreCompletion.completed_at >= reset_time
            )
        ).order_by(ChoreCompletion.completed_at.desc()).first()
        
        chore_states.append({
            "id": chore.id,
            "description": chore.description,
            "completed": bool(latest_completion),
            "completed_by": latest_completion.staff_name if latest_completion else None,
            "completed_at": latest_completion.completed_at if latest_completion else None,
            "comment": latest_completion.comment if latest_completion else None
        })
    
    return chore_states

@app.post("/api/chore_completion")
async def complete_chore(request: ChoreCompletionRequest, db: Session = Depends(get_db)):
    try:
        chore = db.query(Chore).filter(Chore.id == request.chore_id).first()
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")

        # Get the latest completion for this chore
        latest_completion = db.query(ChoreCompletion).filter(
            ChoreCompletion.chore_id == request.chore_id
        ).order_by(ChoreCompletion.completed_at.desc()).first()

        if request.completed:
            # Try to send notification first
            await telegram.notify_chore_completion(request.staff_name, chore.description)
            
            # If notification succeeds, update database
            completion = ChoreCompletion(
                chore_id=request.chore_id,
                staff_name=request.staff_name,
                completed_at=datetime.now(cet_tz)
            )
            db.add(completion)
            
            # If there was a previous completion, delete it
            if latest_completion:
                db.delete(latest_completion)
                
            db.commit()
        else:
            # If unchecking and there is a completion
            if latest_completion:
                # Try to send notification first
                await telegram.notify_chore_uncomplete(request.staff_name, chore.description)
                
                # If notification succeeds, update database
                db.delete(latest_completion)
                db.commit()

        return {"status": "success"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error in complete_chore: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chore_comment")
async def add_chore_comment(request: ChoreCommentRequest, db: Session = Depends(get_db)):
    completion = db.query(ChoreCompletion).filter(
        ChoreCompletion.chore_id == request.chore_id
    ).order_by(ChoreCompletion.completed_at.desc()).first()

    if completion:
        completion.comment = request.comment
        db.commit()

    return {"status": "success"}

@app.post("/api/submit_checklist")
async def submit_checklist(request: ChecklistSubmission, db: Session = Depends(get_db)):
    checklist = db.query(Checklist).filter(Checklist.name == request.checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Get all chores and their completion status
    now = datetime.now(cet_tz)
    if request.checklist_id == "weekly":
        reset_time = get_last_weekly_reset_time(now)
    else:
        reset_time = get_last_reset_time(now)
    
    # Get all completed chores since last reset
    completed_chores = db.query(ChoreCompletion).join(Chore).filter(
        and_(
            Chore.checklist_id == checklist.id,
            ChoreCompletion.completed_at >= reset_time
        )
    ).order_by(ChoreCompletion.completed_at).all()

    # Save signature
    signature = Signature(
        checklist_id=checklist.id,
        staff_name=request.staff_name,
        signature_data=request.signature_data,
        completed_at=datetime.now(cet_tz)
    )
    db.add(signature)
    db.commit()

    # Send Telegram notifications
    # First send individual completion summary
    completion_summary = f"🏁 {request.staff_name} completed {len(completed_chores)} tasks in {checklist.name.upper()}:\n"
    for completion in completed_chores:
        time_str = completion.completed_at.astimezone(cet_tz).strftime("%H:%M")
        completion_summary += f"\n✓ {completion.chore.description} ({time_str})"
    await telegram.send_message(completion_summary)

    # Then send final completion notification
    await telegram.notify_checklist_completion(request.staff_name, checklist.name.upper())

    return {"status": "success"}

# Telegram webhook endpoint
@app.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming updates from Telegram."""
    logger.info("Received Telegram update")
    try:
        await telegram.handle_update(update.dict())
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing Telegram update: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Test Telegram endpoint
@app.get("/telegram/test")
async def test_telegram():
    """Test Telegram notifications."""
    try:
        # Log environment variables (excluding sensitive data)
        env_vars = {k: '***' if 'TOKEN' in k else v for k, v in os.environ.items()}
        logger.info(f"Current environment variables: {env_vars}")
        
        # Try to send a test message
        await telegram.send_message("🔔 Test notification from Castle Pub Checklist")
        
        return {
            "status": "ok",
            "message": "Test notification sent",
            "bot_token_present": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "chat_id_present": bool(os.getenv("TELEGRAM_CHAT_ID"))
        }
    except Exception as e:
        logger.error(f"Error testing Telegram: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
                "bot_token_present": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
                "chat_id_present": bool(os.getenv("TELEGRAM_CHAT_ID"))
            }
        )

# Manual webhook setup endpoint
@app.get("/telegram/setup")
async def setup_telegram():
    """Manually trigger Telegram bot setup."""
    try:
        webhook_info = await telegram.get_webhook_info()
        logger.info(f"Current webhook info: {webhook_info}")
        
        await telegram._setup_bot()
        
        new_webhook_info = await telegram.get_webhook_info()
        logger.info(f"New webhook info: {new_webhook_info}")
        
        return {
            "status": "ok",
            "previous_webhook": webhook_info,
            "current_webhook": new_webhook_info
        }
    except Exception as e:
        logger.error(f"Error setting up Telegram webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Webhook info endpoint
@app.get("/telegram/status")
async def telegram_status():
    """Get current Telegram webhook status."""
    try:
        webhook_info = await telegram.get_webhook_info()
        return {
            "status": "ok",
            "webhook_info": webhook_info
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    # Always return healthy during startup
    if not is_db_ready:
        return {
            "status": "starting",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        # Quick connection test
        await test_db_connection()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Database health check endpoint - separate from main health check
@app.get("/health/database")
async def database_health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database_error": str(e)}
        )

# Add new reset endpoint
@app.post("/api/admin/reset-database")
async def reset_database(db: Session = Depends(get_db)):
    try:
        # First delete all existing data in the correct order
        db.query(Signature).delete()
        db.query(ChoreCompletion).delete()
        db.query(Chore).delete()
        db.query(Checklist).delete()
        db.commit()
        
        # Now seed the database with fresh data
        seed_database(db)
        db.commit()
        
        return {
            "status": "success",
            "message": "Database reset successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database reset: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

# Add this new endpoint
@app.post("/api/reset_checklist/{checklist_name}")
async def reset_checklist(checklist_name: str, db: Session = Depends(get_db)):
    try:
        # Get the checklist
        checklist = db.query(Checklist).filter(Checklist.name == checklist_name).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        # Delete all completions for this checklist's chores
        chore_ids = [chore.id for chore in checklist.chores]
        db.query(ChoreCompletion).filter(ChoreCompletion.chore_id.in_(chore_ids)).delete(synchronize_session=False)
        
        # Delete any signatures for this checklist
        db.query(Signature).filter(Signature.checklist_id == checklist.id).delete(synchronize_session=False)
        
        db.commit()
        
        # Send notification about the reset
        await telegram.send_message(f"⚠️ {checklist_name.upper()} checklist has been manually reset")
        
        return {"status": "success", "message": f"Checklist {checklist_name} has been reset"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting checklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

@app.post("/api/chores/{chore_id}/toggle")
async def toggle_chore(chore_id: int, data: dict, db: Session = Depends(get_db)):
    chore = db.query(Chore).filter(Chore.id == chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")

    # Toggle completion status
    chore.completed = not chore.completed
    chore.completed_by = data.get("staff_name") if chore.completed else None
    chore.completed_at = datetime.utcnow() if chore.completed else None

    # Send Telegram notification
    if chore.completed:
        message = f"✅ <b>{data.get('staff_name')}</b> completed: {chore.description}"
        send_telegram_message(message)

    db.commit()
    return {"completed": chore.completed}

@app.post("/api/sections/{section_id}/complete")
async def complete_section(section_id: int, data: dict, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Get all uncompleted chores in the section
    uncompleted_chores = db.query(Chore).filter(
        Chore.section_id == section_id,
        Chore.completed == False
    ).all()

    # Mark all chores as completed
    staff_name = data.get("staff_name")
    completed_at = datetime.utcnow()
    
    for chore in uncompleted_chores:
        chore.completed = True
        chore.completed_by = staff_name
        chore.completed_at = completed_at

    # Send Telegram notification for the section
    message = f"✅ <b>{staff_name}</b> completed the {section.name} section!"
    send_telegram_message(message)

    db.commit()
    return {"completed": True, "chores_completed": len(uncompleted_chores)} 