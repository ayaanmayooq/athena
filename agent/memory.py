import json
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from openai import OpenAI

from .config import EMBEDDING_MODEL

MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "athena_memory.jsonl",
)
_embedding_client = OpenAI()


def _read_all_entries() -> List[Dict[str, Any]]:
    if not os.path.exists(MEMORY_FILE):
        return []

    entries: List[Dict[str, Any]] = []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _build_embedding_input(kind: str, content: str, meta: Dict[str, Any]) -> str:
    parts: List[str] = []
    if kind:
        parts.append(f"[{kind}]")
    if content:
        parts.append(content)
    if meta:
        try:
            parts.append(json.dumps(meta, sort_keys=True, ensure_ascii=False))
        except TypeError:
            parts.append(str(meta))
    return " | ".join(part.strip() for part in parts if part and part.strip())


def _get_embedding(text: str) -> Optional[List[float]]:
    text = text.strip()
    if not text:
        return None
    try:
        response = _embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception:
        return None


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> Optional[float]:
    if len(vec_a) != len(vec_b):
        return None

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a == 0.0 or norm_b == 0.0:
        return None

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def add_memory(kind: str, content: str, meta: Optional[Dict[str, Any]] = None) -> str:
    """Store a memory entry with optional embedding."""
    meta = meta or {}
    embedding_input = _build_embedding_input(kind, content, meta)
    embedding = _get_embedding(embedding_input)

    entry: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "kind": kind,
        "content": content,
        "meta": meta,
    }
    if embedding is not None:
        entry["embedding"] = embedding

    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return f"Memory stored: {kind} - {content[:50]}..."


def get_recent(limit: int = 10) -> List[Dict[str, Any]]:
    """Return the most recent memory entries (newest first)."""
    if limit <= 0:
        return []

    entries = _read_all_entries()
    if not entries:
        return []

    return list(reversed(entries[-limit:]))


def get_relevant(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Return memories most relevant to the query using cosine similarity."""
    if limit <= 0:
        return []

    query_embedding = _get_embedding(query)
    if query_embedding is None:
        return []

    results: List[Dict[str, Any]] = []
    for entry in _read_all_entries():
        embedding = entry.get("embedding")
        if not isinstance(embedding, list):
            continue
        similarity = _cosine_similarity(query_embedding, embedding)
        if similarity is None:
            continue
        enriched_entry = dict(entry)
        enriched_entry["score"] = similarity
        results.append(enriched_entry)

    results.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return results[:limit]


def format_memories_for_display(memories: List[Dict[str, Any]], *, show_scores: bool = False) -> str:
    """Format memory entries for display back to the model/user."""
    if not memories:
        return "No memories found."

    lines: List[str] = []
    for mem in memories:
        timestamp = mem.get("timestamp", "unknown")
        kind = mem.get("kind", "unknown")
        content = mem.get("content", "")
        line = f"[{timestamp}] {kind}: {content}"
        score = mem.get("score")
        if show_scores and isinstance(score, (int, float)):
            line += f" (score: {score:.3f})"
        lines.append(line)

    return "\n".join(lines)
