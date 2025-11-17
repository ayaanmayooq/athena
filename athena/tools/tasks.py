from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from athena.core.tool_base import tool
from athena.memory.db import get_session
from athena.memory.models import TaskORM


@tool(
    name="create_task",
    description="Create a new task for the current user.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string", "nullable": True},
            "due_date": {
                "type": "string",
                "description": "ISO datetime string",
                "nullable": True,
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "nullable": True,
            },
        },
        "required": ["user_id", "title"],
    },
)
def create_task(
    user_id: str,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    session = get_session()
    dt = None
    if due_date:
        dt = datetime.fromisoformat(due_date)
    task = TaskORM(
        user_id=user_id,
        title=title,
        description=description,
        due_date=dt,
        tags={"tags": tags} if tags else None,
    )
    session.add(task)
    session.commit()
    task_id = task.id
    session.close()
    return {"status": "ok", "id": task_id}


@tool(
    name="list_tasks",
    description="List tasks for the current user.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["pending", "done"],
                "nullable": True,
            },
        },
        "required": ["user_id"],
    },
)
def list_tasks(
    user_id: str,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    session = get_session()
    q = session.query(TaskORM).filter(TaskORM.user_id == user_id)
    if status:
        q = q.filter(TaskORM.status == status)
    rows = q.order_by(TaskORM.created_at.desc()).all()
    tasks = [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "status": r.status,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "tags": r.tags,
        }
        for r in rows
    ]
    session.close()
    return tasks
