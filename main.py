from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set in environment variables")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Notes table
class NoteModel(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

# Create table (runs at startup)
Base.metadata.create_all(bind=engine)

# FastAPI app with explicit docs
app = FastAPI(
    title="Notes App API",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI explicitly enabled
    redoc_url=None         # Disable ReDoc (optional)
)

# Pydantic schemas
class Note(BaseModel):
    title: str
    content: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.post("/notes/", response_model=Note)
def create_note(note: Note):
    db = next(get_db())
    note_id = str(uuid.uuid4())
    db_note = NoteModel(id=note_id, title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return note

@app.get("/notes/", response_model=List[Note])
def list_notes():
    db = next(get_db())
    notes = db.query(NoteModel).all()
    return [Note(title=n.title, content=n.content) for n in notes]

@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: str):
    db = next(get_db())
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(title=note.title, content=note.content)

