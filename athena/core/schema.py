from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    role: Role
    content: str
    tool_name: Optional[str] = None
    created_at: Optional[datetime] = None
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None


class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ToolSchema(BaseModel):
    type: Literal["function"] = "function"
    function: Dict[str, Any]
