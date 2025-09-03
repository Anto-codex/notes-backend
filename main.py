from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI(title="Notes App API", version="1.0.0")

# Temporary storage (later you can switch to DB)
notes = {}

# Request/Response Model
class Note(BaseModel):
    title: str
    content: str

class NoteResponse(Note):
    id: str
    share_url: str

@app.post("/notes", response_model=NoteResponse)
def create_note(note: Note):
    note_id = str(uuid.uuid4())
    share_url = f"/share/{note_id}"
    notes[note_id] = {"id": note_id, "title": note.title, "content": note.content, "share_url": share_url}
    return notes[note_id]

@app.get("/notes", response_model=List[NoteResponse])
def get_notes():
    return list(notes.values())

@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: str):
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return notes[note_id]

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: str, note: Note):
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    notes[note_id].update({"title": note.title, "content": note.content})
    return notes[note_id]

@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    del notes[note_id]
    return {"success": True}

@app.get("/share/{note_id}", response_model=NoteResponse)
def share_note(note_id: str):
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return notes[note_id]
