from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")  # fallback for local testing

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Notes table
class NoteModel(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Notes App API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Pydantic schema
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
@app.get("/")
def root():
    return {"message": "Notes API is live 🚀"}

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
    return [Note(title=n.title, content=n.content, id=n.id) if hasattr(n, 'id') else Note(title=n.title, content=n.content) for n in notes]

@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: str):
    db = next(get_db())
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(title=note.title, content=note.content)

@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    db = next(get_db())
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": f"Note {note_id} deleted successfully"}
