from .base import Tool
from .notes import take_note_tool, list_notes_tool
from .system_ops import open_app_tool
from .web_search import web_search_tool
from .memory import remember_tool, recall_recent_tool, recall_relevant_tool

ALL_TOOLS: dict[str, Tool] = {
    t.name: t for t in [
        take_note_tool,
        list_notes_tool,
        open_app_tool,
        web_search_tool,
        remember_tool,
        recall_recent_tool,
        recall_relevant_tool,
    ]
}

def get_tool_schemas_for_openai():
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
            },
        }
        for tool in ALL_TOOLS.values()
    ]
