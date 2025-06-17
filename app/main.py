from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, and_, func
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, time, timedelta
import os
import asyncio
from contextlib import asynccontextmanager
import logging
import pytz
import requests
from sqlalchemy import inspect
import pdfkit
import dropbox
from jinja2 import Environment, FileSystemLoader
import tempfile
import json

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
from .admin import router as admin_router  # Import the admin router

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

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Application startup
    logger.info("Application startup initiated")
    
    # Create tables if they don't exist
    try:
        logger.info("Creating database tables...")
        init_db()
        logger.info("Database tables created successfully")
        
        # Seed database if empty
        logger.info("Checking if database needs seeding...")
        db = SessionLocal()
        try:
            # Check if tables exist by querying the checklists table
            logger.info("Checking if checklists table exists...")
            result = db.execute(text("SELECT COUNT(*) FROM checklists"))
            count = result.scalar()
            logger.info(f"Found {count} checklists in database")
            
            if count == 0:
                logger.info("Database is empty, seeding initial data...")
                seed_database(db)
                db.commit()
                logger.info("Database seeded successfully")
            else:
                logger.info(f"Database already contains {count} checklists, skipping seeding")
        except Exception as e:
            logger.error(f"Error during database seeding: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            logger.info("Database session closed after seeding")
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}", exc_info=True)
        raise
    
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

# Include the admin router
app.include_router(admin_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main checklist interface."""
    return templates.TemplateResponse("index.html", {"request": request})

# Health check endpoints
@app.get("/up")
async def health_check():
    """Health check endpoint for Railway."""
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
    generate_pdf: bool = False
    save_to_dropbox: bool = False

class TelegramUpdate(BaseModel):
    """Simplified Telegram Update model"""
    update_id: int
    message: Optional[dict] = None

def get_last_reset_time(checklist_name: str, db: Session) -> Optional[datetime]:
    """Get the last reset time for a checklist."""
    try:
        # Get the most recent signature for this checklist
        last_signature = db.query(Signature).filter(
            Signature.checklist_id == db.query(Checklist.id).filter(Checklist.name == checklist_name).scalar()
        ).order_by(Signature.completed_at.desc()).first()
        
        if last_signature:
            return last_signature.completed_at
        return None
    except Exception as e:
        logger.error(f"Error getting last reset time: {str(e)}", exc_info=True)
        return None

@app.get("/api/checklists/{checklist_name}/chores")
def get_checklist_chores(checklist_name: str, db: Session = Depends(get_db)):
    """Get all chores for a checklist with their completion status."""
    try:
        logger.info(f"Getting chores for checklist: {checklist_name}")
        
        # Get checklist and sections in a single query with eager loading
        checklist = (
            db.query(Checklist)
            .filter(Checklist.name == checklist_name)
            .options(joinedload(Checklist.sections))
            .first()
        )
        
        if not checklist:
            logger.error(f"Checklist not found: {checklist_name}")
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        sections = sorted(checklist.sections, key=lambda s: s.order or 0)
        logger.info(f"Found {len(sections)} sections")
        
        # Get all chores for this checklist
        chores = (
            db.query(Chore)
            .filter(Chore.section_id.in_([s.id for s in sections]))
            .order_by(Chore.order)
            .all()
        )
        
        logger.info(f"Found {len(chores)} chores")
        
        # Process the results
        chore_list = []
        for chore in chores:
            section = next(s for s in sections if s.id == chore.section_id)
            chore_data = {
                "id": chore.id,
                "description": chore.description,
                "order": chore.order,
                "section": section.name,
                "section_id": section.id,
                "completed": chore.completed,
                "completed_by": chore.completed_by,
                "completed_at": chore.completed_at.isoformat() if chore.completed_at else None,
                "comment": None  # We'll add comment support later if needed
            }
            chore_list.append(chore_data)
        
        logger.info(f"Successfully processed {len(chore_list)} chores")
        return chore_list
        
    except Exception as e:
        logger.error(f"Error processing chores: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chore_completion")
async def complete_chore(request: ChoreCompletionRequest, db: Session = Depends(get_db)):
    """Mark a chore as completed or uncompleted."""
    try:
        # Get the chore
        chore = db.query(Chore).filter(Chore.id == request.chore_id).first()
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")
        
        # Get the checklist name for this chore
        checklist = db.query(Checklist).join(Section).join(Chore).filter(Chore.id == request.chore_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        # Get the last reset time
        last_reset = get_last_reset_time(checklist.name, db)
        
        # Check if we're within the reset window
        now = datetime.now(cet_tz)
        if last_reset:
            last_reset = last_reset.astimezone(cet_tz)
            reset_start = datetime.combine(now.date(), RESET_START_TIME, tzinfo=cet_tz)
            reset_end = datetime.combine(now.date(), RESET_END_TIME, tzinfo=cet_tz)
            
            if reset_start <= now <= reset_end and last_reset.date() == now.date():
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify chores during reset window (6:00-8:00 AM)"
                )
        
        # Create or update completion
        completion = db.query(ChoreCompletion).filter(
            ChoreCompletion.chore_id == request.chore_id,
            ChoreCompletion.staff_name == request.staff_name
        ).first()
        
        if completion:
            # Update existing completion
            completion.completed = request.completed
            completion.completed_at = datetime.now(cet_tz)
            if hasattr(request, 'comment') and request.comment:
                completion.comment = request.comment
        else:
            # Create new completion
            completion = ChoreCompletion(
                chore_id=request.chore_id,
                staff_name=request.staff_name,
                completed=request.completed,
                completed_at=datetime.now(cet_tz),
                comment=getattr(request, 'comment', None)
            )
            db.add(completion)
        
        db.commit()
        
        # Send Telegram notification
        if request.completed:
            message = f"✅ {request.staff_name} completed: {chore.description}"
            send_telegram_message(message)
        else:
            message = f"❌ {request.staff_name} uncompleted: {chore.description}"
            send_telegram_message(message)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error completing chore: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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

def generate_pdf_report(checklist: Checklist, staff_name: str, db: Session) -> str:
    """Generate a PDF report for the completed checklist."""
    try:
        # Get all sections and chores
        sections = db.query(Section).filter(Section.checklist_id == checklist.id).order_by(Section.order).all()
        chores_by_section = {}
        
        for section in sections:
            chores = db.query(Chore).filter(Chore.section_id == section.id).order_by(Chore.order).all()
            chores_with_completion = []
            for chore in chores:
                completion = db.query(ChoreCompletion).filter(
                    ChoreCompletion.chore_id == chore.id
                ).order_by(ChoreCompletion.completed_at.desc()).first()
                
                chores_with_completion.append({
                    'description': chore.description,
                    'completed': completion.completed if completion else False,
                    'completed_by': completion.staff_name if completion else None,
                    'completed_at': completion.completed_at.strftime('%Y-%m-%d %H:%M:%S') if completion and completion.completed_at else None,
                    'comment': completion.comment if completion else None
                })
            
            chores_by_section[section.name] = chores_with_completion

        # Load template
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('checklist_report.html')
        
        # Render HTML
        html_content = template.render(
            checklist_name=checklist.name,
            staff_name=staff_name,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            sections=chores_by_section
        )
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Generate PDF
            pdfkit.from_string(html_content, tmp.name)
            return tmp.name
            
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

def upload_to_dropbox(file_path: str, checklist_name: str, staff_name: str) -> str:
    """Upload a file to Dropbox and return the shared link."""
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))
        
        # Create folder path
        folder_path = f"/checklist_reports/{datetime.now().strftime('%Y-%m-%d')}"
        
        # Upload file
        file_name = f"{checklist_name}_{staff_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(file_path, 'rb') as f:
            dbx.files_upload(f.read(), f"{folder_path}/{file_name}")
        
        # Create shared link
        shared_link = dbx.sharing_create_shared_link(f"{folder_path}/{file_name}")
        return shared_link.url
        
    except Exception as e:
        logger.error(f"Error uploading to Dropbox: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload to Dropbox")

@app.post("/api/submit_checklist")
async def submit_checklist(submission: ChecklistSubmission, db: Session = Depends(get_db)):
    """Submit a completed checklist."""
    try:
        logger.info(f"Received checklist submission: {submission}")
        
        # Get the checklist
        checklist = db.query(Checklist).filter(Checklist.name == submission.checklist_id).first()
        if not checklist:
            logger.error(f"Checklist not found: {submission.checklist_id}")
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        # Verify all chores are completed
        chores = db.query(Chore).filter(Chore.checklist_id == checklist.id).all()
        for chore in chores:
            completion = db.query(ChoreCompletion).filter(
                ChoreCompletion.chore_id == chore.id
            ).order_by(ChoreCompletion.completed_at.desc()).first()
            
            if not completion or not completion.completed:
                logger.error(f"Chore {chore.id} not completed")
                raise HTTPException(
                    status_code=400,
                    detail="All chores must be completed before submitting the checklist"
                )
        
        pdf_url = None
        if submission.generate_pdf:
            # Generate PDF report
            pdf_path = generate_pdf_report(checklist, submission.staff_name, db)
            
            if submission.save_to_dropbox:
                # Upload to Dropbox
                pdf_url = upload_to_dropbox(pdf_path, submission.checklist_id, submission.staff_name)
            
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        # Notify via Telegram
        try:
            logger.info("Preparing to send Telegram notification")
            message = f"✅ Checklist '{submission.checklist_id}' completed by {submission.staff_name}"
            if pdf_url:
                message += f"\n📄 Report: {pdf_url}"
            logger.info(f"Sending Telegram message: {message}")
            
            # Log Telegram configuration
            logger.info(f"Telegram bot token present: {bool(os.getenv('TELEGRAM_BOT_TOKEN'))}")
            logger.info(f"Telegram chat ID present: {bool(os.getenv('TELEGRAM_CHAT_ID'))}")
            
            success = await telegram.notify_checklist_completion(
                staff_name=submission.staff_name,
                checklist_name=submission.checklist_id,
                message=message
            )
            
            if not success:
                logger.error("Failed to send Telegram notification")
            else:
                logger.info("Telegram notification sent successfully")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}", exc_info=True)
            # Continue even if Telegram notification fails
        
        # Don't reset the checklist, just return success
        return {
            "status": "success",
            "message": "Checklist submitted successfully",
            "pdf_url": pdf_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit checklist")

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
    """Reset and reseed the database."""
    try:
        logger.info("Starting database reset")
        
        # Drop all tables
        logger.info("Dropping all tables")
        Base.metadata.drop_all(bind=engine)
        
        # Create tables with new schema
        logger.info("Creating tables with new schema")
        Base.metadata.create_all(bind=engine)
        
        # Add new columns to chores table
        logger.info("Adding new columns to chores table")
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed_by VARCHAR"))
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))
                conn.commit()
                logger.info("Added new columns successfully")
            except Exception as e:
                logger.warning(f"Could not add new columns: {str(e)}")
        
        # Reseed database
        logger.info("Reseeding database")
        seed_database(db)
        
        logger.info("Database reset and reseeded successfully")
        return {"status": "success", "message": "Database reset and reseeded successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset_checklist/{checklist_name}")
async def reset_checklist(checklist_name: str, request: Request, db: Session = Depends(get_db)):
    """Reset a checklist by clearing all completion records."""
    try:
        # Get the checklist
        checklist = db.query(Checklist).filter(Checklist.name == checklist_name).first()
        if not checklist:
            raise HTTPException(status_code=404, detail=f"Checklist {checklist_name} not found")

        # Get request body
        body = await request.json()
        staff_name = body.get('staff_name', 'Someone')

        # Get all sections for this checklist
        sections = db.query(Section).filter(Section.checklist_id == checklist.id).all()
        
        # Get all chores for these sections
        section_ids = [section.id for section in sections]
        chores = db.query(Chore).filter(Chore.section_id.in_(section_ids)).all()
        
        # Reset all chores
        for chore in chores:
            chore.completed = False
            chore.completed_by = None
            chore.completed_at = None
        
        # Commit the changes
        db.commit()

        # Send Telegram notification
        message = f"{staff_name} reset the {checklist_name} checklist"
        send_telegram_message(message)

        return {"message": "Checklist reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting checklist: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def send_telegram_message(message: str):
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram configuration missing, skipping notification")
        return

    # Add timestamp to message
    now = datetime.now(cet_tz)
    time_str = now.strftime("%H:%M")
    message = f"{message} at {time_str}"

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
        logger.error(f"Failed to send Telegram message: {str(e)}")
        # Don't raise the exception, just log it

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/checklist")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Modify the chore completion endpoint to broadcast updates
@app.post("/api/chores/{chore_id}/toggle")
async def toggle_chore(chore_id: int, data: dict, db: Session = Depends(get_db)):
    try:
        chore = db.query(Chore).filter(Chore.id == chore_id).first()
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")

        # Update chore completion
        chore.completed = data.get("completed", False)
        chore.completed_by = data.get("staff_name") if chore.completed else None
        chore.completed_at = datetime.now() if chore.completed else None

        db.commit()

        # Broadcast the update to all connected clients
        await manager.broadcast({
            "type": "chore_update",
            "chore_id": chore_id,
            "completed": chore.completed,
            "completed_by": chore.completed_by,
            "completed_at": chore.completed_at.isoformat() if chore.completed_at else None
        })

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error toggling chore: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sections/{section_id}/complete")
async def complete_section(section_id: int, data: dict, db: Session = Depends(get_db)):
    """Complete all chores in a section."""
    try:
        # Get the section
        section = db.query(Section).filter(Section.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        
        # Get the checklist for this section
        checklist = db.query(Checklist).filter(Checklist.id == section.checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        # Get the last reset time
        last_reset = get_last_reset_time(checklist.name, db)
        
        # Check if we're within the reset window
        now = datetime.now(cet_tz)
        if last_reset:
            last_reset = last_reset.astimezone(cet_tz)
            reset_start = datetime.combine(now.date(), RESET_START_TIME, tzinfo=cet_tz)
            reset_end = datetime.combine(now.date(), RESET_END_TIME, tzinfo=cet_tz)
            
            if reset_start <= now <= reset_end and last_reset.date() == now.date():
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify chores during reset window (6:00-8:00 AM)"
                )
        
        # Get all chores in the section
        chores = db.query(Chore).filter(Chore.section_id == section_id).all()
        
        # Get staff name from request
        staff_name = data.get("staff_name")
        if not staff_name:
            raise HTTPException(status_code=400, detail="Staff name is required")
        
        # Complete all chores in the section
        comments = []
        for chore in chores:
            # Create or update completion
            completion = db.query(ChoreCompletion).filter(
                ChoreCompletion.chore_id == chore.id,
                ChoreCompletion.staff_name == staff_name
            ).first()
            
            if completion:
                # Update existing completion
                completion.completed = True
                completion.completed_at = datetime.now(cet_tz)
                if data.get('comment'):
                    completion.comment = data.get('comment')
                    comments.append(f"• {chore.description}: {data.get('comment')}")
            else:
                # Create new completion
                completion = ChoreCompletion(
                    chore_id=chore.id,
                    staff_name=staff_name,
                    completed=True,
                    completed_at=datetime.now(cet_tz),
                    comment=data.get('comment')
                )
                if data.get('comment'):
                    comments.append(f"• {chore.description}: {data.get('comment')}")
                db.add(completion)
        
        db.commit()
        
        # Send single Telegram notification for the entire section
        time_str = datetime.now(cet_tz).strftime("%H:%M")
        message = f"✅ {staff_name} completed section '{section.name}' at {time_str}"
        if comments:
            message += "\nComments:\n" + "\n".join(comments)
        send_telegram_message(message)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error completing section: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/db-state")
async def debug_db_state(db: Session = Depends(get_db)):
    """Debug endpoint to check database state."""
    try:
        # Check checklists
        checklists = db.query(Checklist).all()
        checklist_data = []
        for checklist in checklists:
            sections = db.query(Section).filter(Section.checklist_id == checklist.id).all()
            section_data = []
            for section in sections:
                chores = db.query(Chore).filter(Chore.section_id == section.id).all()
                section_data.append({
                    "id": section.id,
                    "name": section.name,
                    "order": section.order,
                    "chores": [{"id": c.id, "description": c.description, "order": c.order} for c in chores]
                })
            checklist_data.append({
                "id": checklist.id,
                "name": checklist.name,
                "description": checklist.description,
                "sections": section_data
            })
        
        return {
            "status": "ok",
            "checklists": checklist_data
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/debug/db")
async def debug_db(db: Session = Depends(get_db)):
    """Debug endpoint to check database state."""
    try:
        checklists = db.query(Checklist).all()
        sections = db.query(Section).all()
        chores = db.query(Chore).all()
        staff = db.query(Staff).all()
        
        return {
            "checklists": [{"id": c.id, "name": c.name, "description": c.description} for c in checklists],
            "sections": [{"id": s.id, "name": s.name, "checklist_id": s.checklist_id} for s in sections],
            "chores": [{"id": c.id, "description": c.description, "section_id": c.section_id} for c in chores],
            "staff": [{"id": s.id, "name": s.name, "is_active": s.is_active} for s in staff],
            "counts": {
                "checklists": len(checklists),
                "sections": len(sections),
                "chores": len(chores),
                "staff": len(staff)
            }
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/reset-db")
async def reset_db_endpoint(db: Session = Depends(get_db)):
    """Temporary endpoint to reset and reseed the database."""
    try:
        from app.models import Base
        from app.database import engine
        from app.seed_data import seed_database
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate tables
        Base.metadata.create_all(bind=engine)
        
        # Reseed database
        seed_database(db)
        
        return {"status": "success", "message": "Database reset and reseeded successfully"}
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {str(e)}")

def init_db():
    """Initialize the database."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Add new columns to chores table if they don't exist
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed_by VARCHAR"))
                conn.execute(text("ALTER TABLE chores ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))
                conn.commit()
                logger.info("Added new columns to chores table")
            except Exception as e:
                logger.warning(f"Could not add new columns: {str(e)}")
        
        # Check if database needs seeding
        logger.info("Checking if database needs seeding...")
        with SessionLocal() as db:
            try:
                # Check if checklists table exists and has data
                logger.info("Checking if checklists table exists...")
                checklists = db.query(Checklist).all()
                if checklists:
                    logger.info(f"Found {len(checklists)} checklists in database")
                    logger.info("Database already contains checklists, skipping seeding")
                else:
                    logger.info("Database is empty, seeding initial data...")
                    seed_database(db)
                    db.commit()
                    logger.info("Database seeded successfully")
            except Exception as e:
                logger.error(f"Error checking/seeding database: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

@app.get("/api/checklists")
def get_checklists(db: Session = Depends(get_db)):
    """Get all checklists."""
    try:
        logger.info("Fetching all checklists")
        checklists = db.query(Checklist).all()
        logger.info(f"Found {len(checklists)} checklists")
        return [{"id": c.id, "name": c.name, "description": c.description} for c in checklists]
    except Exception as e:
        logger.error(f"Error fetching checklists: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch checklists")

@app.post("/api/admin/seed")
def manual_seed(db: Session = Depends(get_db)):
    from .seed_data import seed_database
    try:
        seed_database(db)
        return {"message": "Database seeded successfully"}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})

@app.get("/api/staff")
def get_staff(db: Session = Depends(get_db)):
    """Get all staff members."""
    try:
        staff = db.query(Staff.name).all()
        return [name[0] for name in staff]
    except Exception as e:
        logger.error(f"Error getting staff list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get staff list") 