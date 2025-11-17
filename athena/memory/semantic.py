from __future__ import annotations

from typing import Any, Dict, List

from athena.core.llm import LLMClient
from athena.memory.db import get_session
from athena.memory.models import DocumentORM


def save_document(
    user_id: str,
    content: str,
    metadata: Dict[str, Any] | None = None,
    llm: LLMClient | None = None,
) -> int:
    """
    Very simple semantic memory stub:
    - compute embedding via LLMClient
    - store as JSON/text in DB
    """
    client = llm or LLMClient()
    embedding = client.embed([content])[0]

    session = get_session()
    doc = DocumentORM(
        user_id=user_id,
        content=content,
        metadata_json=metadata or {},
        embedding=",".join(str(x) for x in embedding),  # placeholder encoding
    )
    session.add(doc)
    session.commit()
    doc_id = doc.id
    session.close()
    return doc_id


def search_documents(
    user_id: str,
    query: str,
    llm: LLMClient | None = None,
    k: int = 5,
) -> List[DocumentORM]:
    """
    Placeholder search: pulls all docs and does cosine similarity in Python.
    Replace with pgvector later.
    """
    import math

    client = llm or LLMClient()
    query_vec = client.embed([query])[0]

    def parse_embedding(s: str | None) -> List[float]:
        if not s:
            return []
        return [float(x) for x in s.split(",")]

    session = get_session()
    docs = session.query(DocumentORM).filter(DocumentORM.user_id == user_id).all()

    scored: List[tuple[float, DocumentORM]] = []

    def cosine(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return -1.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return -1.0
        return dot / (na * nb)

    for d in docs:
        emb = parse_embedding(d.embedding)
        sim = cosine(query_vec, emb)
        scored.append((sim, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    session.close()
    return [d for _, d in scored[:k]]
