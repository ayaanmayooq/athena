from typing import Optional

from .base import Tool
from agent.memory import (
    add_memory,
    get_recent,
    get_relevant,
    format_memories_for_display,
)


def _remember(kind: str, content: str, meta: Optional[str] = None) -> str:
    """Store a memory for later recall."""
    import json

    meta_dict = None
    if meta:
        try:
            meta_dict = json.loads(meta)
        except json.JSONDecodeError:
            meta_dict = {"raw": meta}

    return add_memory(kind=kind, content=content, meta=meta_dict)


def _recall_recent(limit: int = 10) -> str:
    """Recall recent memories stored by the agent."""
    memories = get_recent(limit=limit)
    return format_memories_for_display(memories)


def _recall_relevant(query: str, limit: int = 5) -> str:
    """Recall memories semantically relevant to the query."""
    memories = get_relevant(query=query, limit=limit)
    return format_memories_for_display(memories, show_scores=True)


remember_tool = Tool(
    name="remember",
    description="Store a memory (fact, preference, event, etc.) for later recall by the agent.",
    parameters_schema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "description": "Type of memory: 'fact', 'preference', 'event', 'task', etc.",
            },
            "content": {
                "type": "string",
                "description": "The actual content to remember",
            },
            "meta": {
                "type": "string",
                "description": "Optional metadata as JSON string",
            },
        },
        "required": ["kind", "content"],
    },
    func=_remember,
)

recall_recent_tool = Tool(
    name="recall_recent",
    description="Recall recent memories stored by the agent. Useful for remembering user facts, preferences, or past events.",
    parameters_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of memories to return",
                "default": 10,
            },
        },
    },
    func=_recall_recent,
)

recall_relevant_tool = Tool(
    name="recall_relevant",
    description="Recall memories most relevant to a query using semantic similarity.",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query describing what to recall",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of memories to return",
                "default": 5,
            },
        },
        "required": ["query"],
    },
    func=_recall_relevant,
)

