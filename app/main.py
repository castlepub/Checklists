from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from .database import get_db
from .models import Checklist, Chore, ChoreCompletion, Signature
from .telegram import telegram

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Castle Checklist App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/checklists/{checklist_id}/chores", response_model=List[ChoreResponse])
async def get_checklist_chores(checklist_id: str, db: Session = Depends(get_db)):
    checklist = db.query(Checklist).filter(Checklist.name == checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    chores = db.query(Chore).filter(Chore.checklist_id == checklist.id).order_by(Chore.order).all()
    return [
        ChoreResponse(
            id=chore.id,
            description=chore.description,
            order=chore.order,
            completed=False,  # Reset completion status each time
            comment=""
        ) for chore in chores
    ]

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
    return {"status": "healthy"} 