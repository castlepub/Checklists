from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Checklist(Base):
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    chores = relationship("Chore", back_populates="checklist")

class Chore(Base):
    __tablename__ = "chores"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"))
    description = Column(String)
    order = Column(Integer)
    checklist = relationship("Checklist", back_populates="chores")
    completions = relationship("ChoreCompletion", back_populates="chore")

class ChoreCompletion(Base):
    __tablename__ = "chore_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    chore_id = Column(Integer, ForeignKey("chores.id"))
    staff_name = Column(String)
    completed_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(Text, nullable=True)
    chore = relationship("Chore", back_populates="completions")

class Signature(Base):
    __tablename__ = "signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"))
    staff_name = Column(String)
    signature_data = Column(Text)  # Base64 encoded PNG
    completed_at = Column(DateTime, default=datetime.utcnow) 