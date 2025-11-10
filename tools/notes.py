import os
from datetime import datetime
from .base import Tool

NOTES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "athena_notes.md",
)

def _take_note(content: str, title: str | None = None) -> str:
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    title = title or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}\n\n")
    return f"Note saved under title '{title}'."

def _list_notes(limit: int = 10) -> str:
    if not os.path.exists(NOTES_FILE):
        return "No notes yet."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-limit * 5:])

take_note_tool = Tool(
    name="take_note",
    description="Append text to a markdown notes file.",
    parameters_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "title": {"type": "string"},
        },
        "required": ["content"],
    },
    func=_take_note,
)

list_notes_tool = Tool(
    name="list_notes",
    description="Show recent notes from the notes file.",
    parameters_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "default": 10}},
    },
    func=_list_notes,
)
