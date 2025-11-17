from __future__ import annotations

from typing import Any, Dict, List, Optional

from athena.core.tool_base import tool
from athena.memory.db import get_session
from athena.memory.models import NoteORM


@tool(
    name="add_note",
    description="Add a note for the current user.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["user_id", "title", "content"],
    },
)
def add_note(user_id: str, title: str, content: str) -> Dict[str, Any]:
    session = get_session()
    note = NoteORM(user_id=user_id, title=title, content=content)
    session.add(note)
    session.commit()
    note_id = note.id
    session.close()
    return {"status": "ok", "id": note_id}


@tool(
    name="search_notes",
    description="Naive search across notes by substring match in title or content.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "query": {"type": "string"},
        },
        "required": ["user_id", "query"],
    },
)
def search_notes(user_id: str, query: str) -> List[Dict[str, Any]]:
    session = get_session()
    q = (
        session.query(NoteORM)
        .filter(NoteORM.user_id == user_id)
        .filter(
            (NoteORM.title.ilike(f"%{query}%"))
            | (NoteORM.content.ilike(f"%{query}%"))
        )
    )
    rows = q.all()
    out = [
        {
            "id": r.id,
            "title": r.title,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    session.close()
    return out
