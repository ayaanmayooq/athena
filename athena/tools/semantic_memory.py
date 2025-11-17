from __future__ import annotations

from typing import Any, Dict, List, Optional

from athena.core.tool_base import tool
from athena.memory import semantic


@tool(
    name="store_knowledge",
    description="Save long-form knowledge (notes, docs, snippets) into the semantic store.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "content": {"type": "string"},
            "metadata": {
                "type": "object",
                "description": "Optional JSON metadata describing the document.",
                "nullable": True,
            },
        },
        "required": ["user_id", "content"],
    },
)
def store_knowledge(
    user_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    doc_id = semantic.save_document(user_id=user_id, content=content, metadata=metadata)
    return {"status": "ok", "id": doc_id}


@tool(
    name="search_knowledge",
    description="Semantic search over stored knowledge snippets (cosine similarity placeholder).",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "query": {"type": "string"},
            "k": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "nullable": True,
            },
        },
        "required": ["user_id", "query"],
    },
)
def search_knowledge(
    user_id: str,
    query: str,
    k: Optional[int] = 5,
) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        return [
            {
                "error": "empty_query",
                "message": "Please provide a short description of what you're searching for.",
            }
        ]
    docs = semantic.search_documents(user_id=user_id, query=query, k=k or 5)
    return [
        {
            "id": d.id,
            "content": d.content,
            "metadata": d.metadata_json,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]
