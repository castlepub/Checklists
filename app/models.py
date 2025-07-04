from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Checklist(Base):
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    chores = relationship("Chore", back_populates="checklist")
    sections = relationship("Section", back_populates="checklist")

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"))
    name = Column(String)
    order = Column(Integer)
    completed = Column(Boolean, default=False)
    checklist = relationship("Checklist", back_populates="sections")
    chores = relationship("Chore", back_populates="section")

class Chore(Base):
    __tablename__ = "chores"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    description = Column(String)
    order = Column(Integer)
    completed = Column(Boolean, default=False)
    completed_by = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    checklist = relationship("Checklist", back_populates="chores")
    section = relationship("Section", back_populates="chores")
    completions = relationship("ChoreCompletion", back_populates="chore")

class ChoreCompletion(Base):
    __tablename__ = "chore_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    chore_id = Column(Integer, ForeignKey("chores.id"))
    staff_name = Column(String)
    completed = Column(Boolean, default=True)
    completed_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(String, nullable=True)
    chore = relationship("Chore", back_populates="completions")

class Signature(Base):
    __tablename__ = "signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"))
    staff_name = Column(String)
    signature_data = Column(Text)  # Base64 encoded PNG
    completed_at = Column(DateTime, default=datetime.utcnow)

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    telegram_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True) 