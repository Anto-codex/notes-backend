from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid
import os

# ------------------------------
# Database setup
# ------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set in environment variables")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Notes table
class NoteModel(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

# Create table
Base.metadata.create_all(bind=engine)

# ------------------------------
# FastAPI app setup
# ------------------------------
app = FastAPI(
    title="Notes App API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Pydantic schemas
# ------------------------------
class Note(BaseModel):
    title: str
    content: str

class NoteResponse(Note):
    id: str

# ------------------------------
# DB session dependency
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------
# Routes
# ------------------------------

# Root endpoint
@app.get("/")
def root():
    return {"message": "Notes API is live 🚀"}

# Create note
@app.post("/notes/", response_model=NoteResponse)
def create_note(note: Note):
    db = next(get_db())
    note_id = str(uuid.uuid4())
    db_note = NoteModel(id=note_id, title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return NoteResponse(id=db_note.id, title=db_note.title, content=db_note.content)

# List all notes
@app.get("/notes/", response_model=List[NoteResponse])
def list_notes():
    db = next(get_db())
    notes = db.query(NoteModel).all()
    return [NoteResponse(id=n.id, title=n.title, content=n.content) for n in notes]

# Get note by ID
@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: str):
    db = next(get_db())
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(id=note.id, title=note.title, content=note.content)

# Update note
@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: str, note: Note):
    db = next(get_db())
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db_note.title = note.title
    db_note.content = note.content
    db.commit()
    db.refresh(db_note)
    return NoteResponse(id=db_note.id, title=db_note.title, content=db_note.content)

# Delete note
@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    db = next(get_db())
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(db_note)
    db.commit()
    return {"message": f"Note {note_id} deleted successfully"}
