from __future__ import annotations

from typing import Any, Dict

from athena.core.tool_base import tool


@tool(
    name="ping",
    description="Simple health check tool that returns 'pong'.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def ping() -> Dict[str, Any]:
    return {"status": "ok", "message": "pong"}


@tool(
    name="echo",
    description="Echo back the given text.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
    },
)
def echo(text: str) -> Dict[str, Any]:
    return {"echo": text}

