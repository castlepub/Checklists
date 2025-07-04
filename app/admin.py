from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Dict
from itertools import groupby
import secrets
import os
import logging
import traceback
from .database import get_db
from .models import Checklist, Chore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

# In a real application, these would be stored securely (e.g., in environment variables)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # Change this in production!

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def group_chores_by_section(chores):
    try:
        # Sort chores by section to prepare for grouping
        sorted_chores = sorted(chores, key=lambda x: (x.section or ""))  # Handle None sections
        # Group chores by section
        grouped = {}
        for section, items in groupby(sorted_chores, key=lambda x: (x.section or "")):
            grouped[section] = list(items)
        return grouped
    except Exception as e:
        logger.error(f"Error in group_chores_by_section: {str(e)}")
        logger.error(traceback.format_exc())
        return {}

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    try:
        logger.info("Fetching checklists from database...")
        checklists = db.query(Checklist).all()
        logger.info(f"Found {len(checklists)} checklists")
        
        # Create a dictionary to store grouped chores for each checklist
        checklist_data = []
        for checklist in checklists:
            try:
                logger.info(f"Processing checklist: {checklist.name}")
                logger.info(f"Number of chores: {len(checklist.chores)}")
                grouped_chores = group_chores_by_section(checklist.chores)
                checklist_data.append({
                    "id": checklist.id,
                    "name": checklist.name,
                    "grouped_chores": grouped_chores
                })
            except Exception as e:
                logger.error(f"Error processing checklist {checklist.name}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
        logger.info("Rendering admin template...")
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "checklists": checklist_data,
                "username": username
            }
        )
    except Exception as e:
        logger.error(f"Error in admin_page: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/checklist/add")
async def add_checklist(
    request: Request,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    form = await request.form()
    name = form.get("name")
    
    if not name:
        raise HTTPException(status_code=400, detail="Checklist name is required")
    
    checklist = Checklist(name=name)
    db.add(checklist)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/admin/checklist/delete/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    checklist = db.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    db.delete(checklist)
    db.commit()
    
    return {"success": True}

@router.get("/admin/chore/{chore_id}")
async def get_chore(
    chore_id: int,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    chore = db.query(Chore).filter(Chore.id == chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    return {
        "id": chore.id,
        "description": chore.description,
        "section": chore.section,
        "order": chore.order
    }

@router.post("/admin/chore/add")
async def add_chore(
    request: Request,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    form = await request.form()
    checklist_id = form.get("checklist_id")
    description = form.get("description")
    section = form.get("section")
    order = form.get("order")
    
    if not all([checklist_id, description, section, order]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    chore = Chore(
        description=description,
        section=section,
        order=int(order),
        checklist_id=int(checklist_id)
    )
    db.add(chore)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/admin/chore/edit")
async def edit_chore(
    request: Request,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    form = await request.form()
    chore_id = form.get("chore_id")
    description = form.get("description")
    section = form.get("section")
    order = form.get("order")
    
    if not all([chore_id, description, section, order]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    chore = db.query(Chore).filter(Chore.id == int(chore_id)).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    chore.description = description
    chore.section = section
    chore.order = int(order)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/admin/chore/delete/{chore_id}")
async def delete_chore(
    chore_id: int,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    chore = db.query(Chore).filter(Chore.id == chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    db.delete(chore)
    db.commit()
    
    return {"success": True} 