from __future__ import annotations

from typing import Any, Dict

from athena.core.config import settings
from athena.core.tool_base import tool


@tool(
    name="system_status",
    description="Return basic Athena system configuration.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def system_status() -> Dict[str, Any]:
    return {
        "chat_model": settings.openai_chat_model,
        "embedding_model": settings.openai_embedding_model,
        "max_history_messages": settings.max_history_messages,
        "database_url": settings.database_url,
    }

