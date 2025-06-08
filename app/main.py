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
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add file handler for persistent logs
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Add stream handler for Railway console output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

# Log all environment variables (except sensitive ones)
env_vars = {k: '***' if 'TOKEN' in k or 'PASSWORD' in k else v for k, v in os.environ.items()}
logger.info(f"Environment variables: {env_vars}")

# Verify required environment variables
required_env_vars = ['DATABASE_URL', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.warning(f"Missing required environment variables: {missing_vars}")

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Application startup
    logger.info("Application startup initiated")
    
    # Create tables if they don't exist
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}", exc_info=True)
        # Don't raise the error - let the app start anyway
    
    yield
    
    # Application shutdown
    logger.info("Application shutdown initiated")
    engine.dispose()
    logger.info("Database connections disposed")

async def seed_database_if_empty():
    """Seed the database if it's empty."""
    try:
        db = SessionLocal()
        try:
            # Check if tables exist by querying the checklists table
            result = db.execute(text("SELECT COUNT(*) FROM checklists"))
            count = result.scalar()
            
            if count == 0:
                logger.info("Database is empty, seeding initial data...")
                seed_database(db)
                db.commit()
                logger.info("Database seeded successfully")
            else:
                logger.info(f"Database already contains {count} checklists, skipping seeding")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}", exc_info=True)

app = FastAPI(
    title="Castle Checklist App",
    lifespan=lifespan,
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main checklist interface."""
    return templates.TemplateResponse("index.html", {"request": request})

# Health check endpoints
@app.get("/up")
async def up_check():
    """Simple health check endpoint that returns immediately."""
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """Comprehensive health check that tests database connection."""
    try:
        # Test database connection with timeout
        db = SessionLocal()
        is_connected = test_db_connection(db)
        db.close()
        
        if not is_connected:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Database connection failed"
                }
            )
        
        # If we get here, database is connected
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("Application startup initiated")

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutdown initiated")

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Start database seeding in background
@app.on_event("startup")
async def seed_database():
    """Start database seeding as a background task."""
    asyncio.create_task(seed_database_if_empty())

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

@app.get("/api/checklists/{checklist_name}/chores")
async def get_checklist_chores(checklist_name: str, db: Session = Depends(get_db)):
    try:
        # Get the checklist
        checklist = db.query(Checklist).filter(Checklist.name == checklist_name).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        # Get all sections for this checklist
        sections = db.query(Section).filter(Section.checklist_id == checklist.id).order_by(Section.order).all()
        
        # Get all chores for this checklist
        chores = db.query(Chore).filter(Chore.checklist_id == checklist.id).order_by(Chore.order).all()
        
        # Get the last reset time
        last_reset = get_last_reset_time()
        
        # Get all completions since last reset
        completions = db.query(ChoreCompletion).filter(
            ChoreCompletion.chore_id.in_([chore.id for chore in chores]),
            ChoreCompletion.completed_at >= last_reset
        ).all()
        
        # Create a map of chore_id to completion
        completion_map = {c.chore_id: c for c in completions}
        
        # Format the response
        response = []
        for chore in chores:
            completion = completion_map.get(chore.id)
            # Find the section for this chore
            section = next((s for s in sections if s.name in chore.description), None)
            section_name = section.name if section else "General Tasks"
            
            response.append({
                "id": chore.id,
                "description": chore.description,
                "order": chore.order,
                "section": section_name,
                "completed": bool(completion),
                "completed_by": completion.completed_by if completion else None,
                "completed_at": completion.completed_at.isoformat() if completion else None,
                "comment": completion.comment if completion else None
            })
        
        return response
    except Exception as e:
        logger.error(f"Error getting checklist chores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chore_completion")
async def complete_chore(request: ChoreCompletionRequest, db: Session = Depends(get_db)):
    # Get the chore
    chore = db.query(Chore).filter(Chore.id == request.chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    # Get the last reset time
    last_reset = get_last_reset_time()
    
    # Check if there's an existing completion
    existing = db.query(ChoreCompletion).filter(
        ChoreCompletion.chore_id == request.chore_id,
        ChoreCompletion.completed_at >= last_reset
    ).first()
    
    if existing:
        # Update existing completion
        existing.completed = request.completed
        existing.completed_by = request.staff_name if request.completed else None
        existing.completed_at = datetime.utcnow() if request.completed else None
        existing.comment = None  # Clear any existing comment
    else:
        # Create new completion
        completion = ChoreCompletion(
            chore_id=request.chore_id,
            completed=request.completed,
            completed_by=request.staff_name if request.completed else None,
            completed_at=datetime.utcnow() if request.completed else None
        )
        db.add(completion)
    
    # Send Telegram notification
    if request.completed:
        await telegram.notify_chore_completion(request.staff_name, chore.description)
    else:
        await telegram.notify_chore_uncomplete(request.staff_name, chore.description)
    
    db.commit()
    return {"status": "success"}

@app.post("/api/chore_comment")
async def add_chore_comment(request: ChoreCommentRequest, db: Session = Depends(get_db)):
    # Get the chore
    chore = db.query(Chore).filter(Chore.id == request.chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    # Get the last reset time
    last_reset = get_last_reset_time()
    
    # Get or create completion
    completion = db.query(ChoreCompletion).filter(
        ChoreCompletion.chore_id == request.chore_id,
        ChoreCompletion.completed_at >= last_reset
    ).first()
    
    if not completion:
        completion = ChoreCompletion(
            chore_id=request.chore_id,
            completed=False,
            completed_at=datetime.utcnow()
        )
        db.add(completion)
    
    # Update comment
    completion.comment = request.comment
    db.commit()
    
    return {"status": "success"}

@app.post("/api/submit_checklist")
async def submit_checklist(request: ChecklistSubmission, db: Session = Depends(get_db)):
    # Get the checklist
    checklist = db.query(Checklist).filter(Checklist.id == request.checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Create signature
    signature = Signature(
        checklist_id=request.checklist_id,
        staff_name=request.staff_name,
        signature_data=request.signature_data,
        signed_at=datetime.utcnow()
    )
    db.add(signature)
    
    # Send Telegram notification
    await telegram.notify_checklist_completion(request.staff_name, checklist.name)
    
    db.commit()
    return {"status": "success"}

@app.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming Telegram webhook updates."""
    try:
        logger.info(f"Received Telegram webhook: {update}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )

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