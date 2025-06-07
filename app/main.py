from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import asyncio
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import get_db, engine, Base, test_db_connection, SessionLocal
from .models import Checklist, Chore, ChoreCompletion, Signature
from .telegram import telegram

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Global variable to track application readiness
is_app_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_app_ready
    logger.info("Application startup initiated")
    
    # Don't wait for database to mark app as ready
    is_app_ready = True
    logger.info("Application marked as ready")
    
    # Start database initialization in the background
    asyncio.create_task(initialize_database())
    
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    engine.dispose()
    logger.info("Database connections disposed")

async def initialize_database():
    """Initialize database in the background"""
    retries = 5
    for i in range(retries):
        try:
            logger.info(f"Database initialization attempt {i + 1}/{retries}")
            await test_db_connection()
            logger.info("Database connection successful")
            
            # Create tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")

            # Check if we need to seed the database
            db = SessionLocal()
            try:
                checklist_count = db.query(Checklist).count()
                if checklist_count == 0:
                    logger.info("No checklists found, seeding database...")
                    from .seed_data import seed_database
                    seed_database(db)
                    logger.info("Database seeded successfully")
                else:
                    logger.info(f"Found {checklist_count} existing checklists, skipping seed")
            finally:
                db.close()
            
            break
        except Exception as e:
            logger.error(f"Database initialization attempt {i + 1} failed: {e}")
            if i < retries - 1:
                logger.info("Retrying database initialization in 5 seconds...")
                await asyncio.sleep(5)

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

# Simple health check endpoint for Railway
@app.get("/up")
async def railway_health_check():
    logger.info("Health check request received at /up")
    return {"status": "ok"}

# Root endpoint with health check support
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Always return ok for Railway health checks
    if request.headers.get("user-agent", "").lower().startswith("railway"):
        logger.info("Railway health check request received at /")
        return JSONResponse({"status": "ok"})
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/checklists/{checklist_id}/chores", response_model=List[ChoreResponse])
async def get_checklist_chores(checklist_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching chores for checklist: {checklist_id}")
        checklist = db.query(Checklist).filter(Checklist.name == checklist_id).first()
        if not checklist:
            logger.error(f"Checklist not found: {checklist_id}")
            raise HTTPException(status_code=404, detail="Checklist not found")
        
        chores = db.query(Chore).filter(Chore.checklist_id == checklist.id).order_by(Chore.order).all()
        logger.info(f"Found {len(chores)} chores for checklist {checklist_id}")
        return [
            ChoreResponse(
                id=chore.id,
                description=chore.description,
                order=chore.order,
                completed=False,  # Reset completion status each time
                comment=""
            ) for chore in chores
        ]
    except Exception as e:
        logger.error(f"Error fetching chores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chores: {str(e)}")

@app.post("/api/chore_completion")
async def complete_chore(request: ChoreCompletionRequest, db: Session = Depends(get_db)):
    chore = db.query(Chore).filter(Chore.id == request.chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")

    if request.completed:
        completion = ChoreCompletion(
            chore_id=request.chore_id,
            staff_name=request.staff_name,
            completed_at=datetime.utcnow()
        )
        db.add(completion)
        db.commit()

        # Send Telegram notification
        await telegram.notify_chore_completion(request.staff_name, chore.description)

    return {"status": "success"}

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

    # Save signature
    signature = Signature(
        checklist_id=checklist.id,
        staff_name=request.staff_name,
        signature_data=request.signature_data,
        completed_at=datetime.utcnow()
    )
    db.add(signature)
    db.commit()

    # Send Telegram notification
    await telegram.notify_checklist_completion(request.staff_name, checklist.name.upper())

    return {"status": "success"}

# Health check endpoint
@app.get("/health")
async def health_check():
    # Always return healthy during startup
    if not is_app_ready:
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